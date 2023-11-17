// use ndarray::prelude::*;
//use pyo3::wrap_pyfunction;
use ndarray::{Array1, Array2, Axis, s, ArrayView1, ArrayView2, linalg::general_mat_vec_mul};
use num::Float;
use pyo3::prelude::*;
use pyo3::exceptions;

// Traduction en rust du code contenu dans le notebook modeledirect_07. Les finctions sont définies de façon similaires 
// à l'exception de celles qui en python renvoient une nouvelle fonction. Dans ce ca si l'implémentation en rust fait intervenir
// une classe sur laquelle est définie une méthode. 

// ** consts ** 

const K_REF: f64 = 0.00001;

const LMBD_REF : f64 = 3.;

const C_REF : f64 = 0.0000004;

const S_REF : f64 = 0.2;

const CW : f64 = 4180.;

const ROWH: f64 = 1000.;


// ** usefull_structs **

struct TimeFunction{
    tss : Array2<f64>,
    dt : f64,
    t0 : f64,
    tf : f64,
}

impl TimeFunction {
    fn return_time(&self, t : f64) -> Array1<f64> {
        if t< self.t0 {
            return self.tss.slice(s![0,..]).to_owned();
        } else if t>= self.tf {
            return self.tss.slice(s![1,..]).to_owned();
        } else {
            let n = ((t - self.t0) / self.dt) as usize;
            let e = (t - self.t0) % self.dt;

            return (1.-e)*self.tss.slice(s![n,..]).to_owned() + e/self.dt*self.tss.slice(s![n+1,..]).to_owned(); 
        }
    }
}

struct FAll{
    u_t : Array2<f64>,
    u_h : Array2<f64>,
    coefs_b_u_t : (f64, f64),
    coefs_b_u_h : (f64, f64),
    d_v : Array1<f64>,
    w_t : Array1<f64>,
    k_t : Array1<f64>,
    j_t : Array1<f64>,
    e_t : Array2<f64>,
    tb : TimeFunction,
    hb : TimeFunction,
}

impl FAll{
    fn compute(&self, time : f64, x : &Array1<f64>) -> Array1<f64>{

        let t = x.slice(s![..self.k_t.dim() -1]);
        let h = x.slice(s![self.k_t.dim() -1..]);

        let h_b = self.hb.return_time(time);
        let forhz = ndarray::concatenate(Axis(0), &[h_b.slice(s![0..1]), h.view(), h_b.slice(s![1..2])]).unwrap(); 
        
        let e_v_t = build_E_V(&self.k_t, &self.d_v, &forhz);
        let v_t = compute_V(&self.d_v, &e_v_t, &self.w_t, &self.j_t);
        let b_v_t = build_B_V(&self.d_v, &e_v_t, &self.w_t, &self.j_t, self.e_t.to_owned(), self.tb.return_time(time));

        let b_u_t = build_B_U(self.coefs_b_u_t, self.e_t.to_owned(), self.tb.return_time(time));
        let b_u_h = build_B_U(self.coefs_b_u_h, self.e_t.to_owned(), self.hb.return_time(time));
    
        
        let t_dot = (self.u_t.clone() + v_t ).dot(&t) + b_u_t + b_v_t;
        let h_dot = self.u_h.clone().dot(&h) + b_u_h;

        ndarray::concatenate(Axis(0), &[t_dot.view(), h_dot.view()]).unwrap()
        
    }
}

struct FSAMPLE{
    y : Array1<f64>,

}

impl FSAMPLE {
    fn echo(&self) -> Array1<f64> {
        self.y.to_owned()
    }
}
// ** array manipulation functions **

fn matrix_vector_product(a: &ArrayView2<f64>, b: &ArrayView1<f64>) -> Array1<f64> {
    let mut result = Array1::zeros(a.rows());
    general_mat_vec_mul(1.0, a, b, 0.0, &mut result);
    result
}

fn norm(a: &ArrayView1<f64>) -> f64 {
    a.dot(a).sqrt()
}

fn diagonal_array(slice: ArrayView1<f64>, diag: isize) -> Array2<f64> {
    let n = slice.len() + diag.abs() as usize;
    let mut mat = Array2::zeros((n, n));
    for (i, &val) in slice.iter().enumerate() {
        let row = i;
        let col = i + n;
        mat[[row, col]] = val;
    }
    mat
}

fn multiply_rows(w: &Array1<f64>, mat: Array2<f64>) -> Array2<f64> {
    let mut result = Array2::zeros(mat.raw_dim());
    for (i, mut row) in result.axis_iter_mut(Axis(0)).enumerate() {
        row *= w[i];
    }
    result
}

// ** build functions **  

fn build_depths_and_sizes(h: f64, n: usize) -> (Array1<f64>, Array1<f64>) {
    let l = h / (n + 1) as f64;
    let sizes = Array1::from_elem(n + 2, l);
    let mut zmeas = Array1::zeros(n);
    zmeas[0] = (sizes[0] + sizes[1]) / 2.0;
    for i in 1..n {
        zmeas[i] = zmeas[i - 1] + (sizes[i] + sizes[i + 1]) / 2.0;
    }
    (zmeas, sizes)
}

fn build_geometry(n: usize, sizes: &Array1<f64>, cw: f64, rhow: f64) -> (Array1<f64>, Array1<f64>, Array1<f64>, Array2<f64>) {
    
    // assert_eq!(sizes.len(), n, "non valid number of given cells sizes");

    
    let D_U = 2.0 * (&sizes.slice(s![..-1]) + &sizes.slice(s![1..])).mapv(|x| x.powi(-1)); 
    let D_V = cw * rhow * (&sizes.slice(s![..-1]) + &sizes.slice(s![1..])).mapv(|x| x.powi(-1));
    let mut e = Array2::zeros((n, 2));
    e[[0, 0]] = 1.0;
    e[[n - 1, 1]] = 1.0;

    (sizes.to_owned(), D_U, D_V, e)
}

fn build_E_V(k : &Array1<f64>, d : &Array1<f64>, h : &Array1<f64>) -> Array1<f64> {
    -k * d * (&h.slice(s![1..]) - &h.slice(s![..-1]))
}

fn build_B_U(coeuf_bu : (f64,f64), e : Array2<f64> , yb : Array1<f64>) -> Array1<f64> {
    let (coef0, coef1) = coeuf_bu;
    coef0 * yb[0]* &e.slice(s![..,0]) + coef1 * yb[1]* &e.slice(s![..,1])
}

fn build_B_V(d : &Array1<f64>, energy : &Array1<f64>, w : &Array1<f64>, j : &Array1<f64>, e : Array2<f64>, yb : Array1<f64>) -> Array1<f64> {
    let (coef0, coef1) = compute_B_V_coefs(d, energy, w, j);
    coef0 * yb[0]* &e.slice(s![..,0]) + coef1 * yb[1]* &e.slice(s![..,1])
}

//  ** compute functions ** 

fn compute_U(d: &Array1<f64>, e: &Array1<f64>, w: &Array1<f64>) -> Array2<f64> {
    let aux = d * e;
    let sub_diag = aux.slice(s![1..-1]);
    let diag = -&aux.slice(s![..-1]) - &aux.slice(s![1..]);
    let sup_diag = aux.slice(s![1..-1]);
    
    let mat = diagonal_array(sub_diag, -1) + diagonal_array(diag.view(), 0) + diagonal_array(sup_diag, 1);
    let u = multiply_rows(w, mat);
    u
}

fn compute_V(d : &Array1<f64> , energies : &Array1<f64>, w : &Array1<f64>, j : &Array1<f64>) -> Array2<f64> {
    
    let aux = d * energies;

    let sub_diag = &j.slice(s![2..-1]) * &aux.slice(s![1..-1]);
    let diag = -&j.slice(s![..-2]) * &aux.slice(s![..-1]) - &j.slice(s![2..])*&aux.slice(s![1..]);
    let sup_diag = &j.slice(s![1..-2]) * &aux.slice(s![1..-1]);

    let mat = diagonal_array(sub_diag.view(), -1) + diagonal_array(diag.view(), 0) + diagonal_array(sup_diag.view(), 1);
    let v = multiply_rows(w, mat);
    v
}

fn compute_B_U_coefs(d: &Array1<f64>, e: &Array1<f64>, w: &Array1<f64>) -> (f64, f64) {
    (&w[0] * &d[0] * &e[0], &w[w.dim() - 1] * &d[d.dim() -1] * &e[e.dim()-1])
}

fn compute_B_V_coefs(d: &Array1<f64>, energy: &Array1<f64>, w: &Array1<f64>, j: &Array1<f64>) -> (f64, f64) {
    let coef0 = &w[0] * &d[0] * &energy[0] * &j[0];
    let coef1 = &w[w.dim() - 1] * &d[d.dim() - 1] * &energy[energy.dim() - 1] * &j[j.dim() - 2];
    (coef0, coef1)
}

fn build_W(c: &Array1<f64>, j: &Array1<f64>) -> Array1<f64> {
    let w = (&c.slice(s![1..-1]) * &j.slice(s![..-1])).mapv(|x| x.powi(-1));
    w
}

fn args_for_F_all(n: usize,sizes: &Array1<f64>,C_T: &Array1<f64>,C_H: &Array1<f64>,lmbd: &Array1<f64>,k: &Array1<f64>) -> (Array2<f64>, Array2<f64>, (f64,f64),(f64,f64), Array1<f64>, Array1<f64>,) {
    let (j, D_U, D_V, e) = build_geometry(n, sizes, 4180. , 1000.);
    let W_T = build_W(C_T, &j);
    let W_H = build_W(C_H, &j);
    let U_T = compute_U(&D_U, lmbd, &W_T);
    let U_H = compute_U(&D_U, k, &W_H);
    let coefs_B_U_T = compute_B_U_coefs(&D_U, lmbd, &W_T);
    let coefs_B_U_H = compute_B_U_coefs(&D_U, k, &W_H);
    (U_T, U_H, coefs_B_U_T, coefs_B_U_H, D_V, W_T)
}

// ** RK5 functions **

fn rk5_coefs(f : &FAll, y : &Array1<f64>, t : f64, h : f64) -> Array2<f64> {


    let mut k = Array2::<f64>::zeros((y.dim(),6));

    let row1 = &f.compute(t, y);
    let row2 = &f.compute( t + h/4. , &((y + h/4.)* row1.to_owned()));
    let row3 = &f.compute(t + 3.*h/8., &((y + 3.*h/32. )* row1.to_owned() + (9.*h/32. )* row2.to_owned()));
    let row4 = &f.compute(t + 12.*h/13., &((y + 1932.*h/2197. )* row1.to_owned() - (7200.*h/2197. )* row2.to_owned() + (7296.*h/2197. )* row3.to_owned()));
    let row5 = &f.compute(t + h, &((y + 439.*h/216. )* row1.to_owned() - (8.*h )* row2.to_owned() + (3680.*h/513. )* row3.to_owned() - (845.*h/4104. )* row4.to_owned()));
    let row6 = &f.compute(t + h/2., &((y - 8.*h/27. )* row1.to_owned() + (2.*h )* row2.to_owned() - (3544.*h/2565. )* row3.to_owned() + (1859.*h/4104. )* row4.to_owned() - (11.*h/40. )* row5.to_owned())); 

    k.slice_mut(s![0,..]).assign(row1);
    k.slice_mut(s![1,..]).assign(row2);
    k.slice_mut(s![2,..]).assign(row3);
    k.slice_mut(s![3,..]).assign(row4);
    k.slice_mut(s![4,..]).assign(row5);
    k.slice_mut(s![5,..]).assign(row6);
    
    k
}

fn step_scaler(k : &ArrayView2<f64>, tol : f64 , rk4_cok : &Array1<f64>, rk5_cok: &Array1<f64>) -> f64 {
    
    let twoN : usize = k.dim().0;
    let  s_t :f64 = tol/(2.*norm(&matrix_vector_product(&k.slice(s![..,..twoN/2]), &rk4_cok.view()).view())).powf(1./4.);
    let s_h :f64 = tol/(2.*norm(&matrix_vector_product(&k.slice(s![twoN/2..,..]), &rk5_cok.view()).view())).powf(1./4.);
    f64::min(s_t,s_h)
}

fn rkf45(f : &FAll, y0 : &Array1<f64>, t0 : f64, tf : f64, h : f64, tol : f64, rk4_cok : &Array1<f64>, rk5_cok : &Array1<f64>, rk5_cok_vec : Array1<f64>) -> Array1<f64> {
    
    let mut t = t0;

    let mut y = y0;

    let  mut result = Array1::<f64>::zeros(y.dim());


    while t<tf {

        let k0 = rk5_coefs(f, y, t, h);

        let mut h_2 = h*step_scaler(&k0.view(), tol, rk4_cok, rk5_cok);

        if t+h_2 > tf {h_2 = tf - t;};

        t = t + h_2;

        let mut k1 = rk5_coefs(f, y, t, h_2);

        general_mat_vec_mul(1.0, &k1, &rk5_cok_vec.view(), 0.0, &mut result);

        let y = &*y + &result;
    }
    y.to_owned()
}
// ** solve **

fn solver(f : &FAll, y0: Array1<f64>, t0 : f64, tol : f64, fsample : &FSAMPLE, times : Array1<f64>, h : f64, method: String ) -> Array2<f64> {
    
    let mut sample = Array2::<f64>::zeros((fsample.echo().dim(),times.dim()));

    if method == "RFK45" {
        let rfk4_cok = Array1::from_vec(vec![25./216., 0., 1408./2565., 2197./4104., -1./5., 0.]);
        let rfk5_cok = Array1::from_vec(vec![16./135., 0., 6656./12825., 28561./56430., -9./50., 2./55.]);

        let mut t = t0.clone();
        let mut y = y0.clone();

        for (i, &time) in times.iter().enumerate() {
            y = rkf45(f.to_owned(), &y, t, time, h as f64, tol, &rfk4_cok, &rfk5_cok, rfk5_cok.clone());

            t = time;

            sample.slice_mut(s![..,i]).assign(&y);


        };

        return sample 
    } else {
        panic!("method not implemented")
    };

}

// ** run ** 

fn steady_state(t0 : f64, tf : f64, tss : &Array2<f64>, hss : &Array2<f64>, arr_t0 : &Array1<f64>, arr_h0 : &Array1<f64>, n : usize, h  : f64 ,k : &Array1<f64>, lmbd: &Array1<f64>, c : &Array1<f64>,s : &Array1<f64>, tol : f64) -> (Array1<f64>, Array2<f64>) {

    let tb = TimeFunction{tss : tss.clone(), dt : tf, t0 : t0, tf : tf};
    let hb = TimeFunction{tss : hss.clone(), dt : tf, t0 : t0, tf : tf};

    let (sizes, zmeas) = build_depths_and_sizes(100., n);

    let ( j, d_u, d_v, e ) = build_geometry(n, &sizes, 4180. , 1000.);

    let (u_t, u_h, coef_but, coef_buh, d_v, w_t ) = args_for_F_all(n, &sizes, c, s, lmbd, k);
    
    let f = FAll{u_t : u_t, u_h : u_h, coefs_b_u_t : coef_but, coefs_b_u_h : coef_buh, d_v : d_v, w_t : w_t, k_t : k.clone(), j_t : j, e_t : e, tb : tb, hb : hb};

    let y0 = ndarray::concatenate(Axis(0), &[arr_t0.view(), arr_h0.view()]).unwrap();

    let fsample = FSAMPLE{y : y0.to_owned()};

    let zmes_result = (zmeas , solver(&f, y0, t0, tol, &fsample, Array1::from(vec![tf]), h, "RFK45".to_string()) );
    zmes_result
}

fn homogeneous(tf : f64 ,tss : Array2<f64> ,hss : Array2<f64>, h : f64, n : usize , arr_t0 : Array1<f64>, arr_h0 :  Array1<f64> ,tol : f64) -> (Array1<f64>, Array2<f64>, Array2<f64>) {

    let mut t0 = 0.;
    let arr_k = Array1::from(vec![1. ; n+1]);
    let arr_lmbd = Array1::from(vec![1. ; n+1]);
    let arr_c = C_REF*Array1::from(vec![1. ; n+1]);
    let arr_s = S_REF*Array1::from(vec![1. ; n+1]);

    let zmes_result = steady_state(t0, tf, &tss, &hss, &arr_t0, &arr_h0, n, h, &arr_k, &arr_lmbd, &arr_c, &arr_s, tol);

    let t_res = zmes_result.1.slice(s![..n,..]).to_owned();
    let h_res = zmes_result.1.slice(s![n..,..]).to_owned();

    let h_ex = (&hss.slice(s![1, ..]) - &hss.slice(s![0, ..])) / h*zmes_result.0.clone() + &hss.slice(s![0, ..]);

    let gamma = -CW * ROWH * K_REF * (&hss.slice(s![1, ..]) - &hss.slice(s![0, ..])) / (h*LMBD_REF);

    let alpha = (&tss.slice(s![0, ..]) - &tss.slice(s![1, ..])) / (1.0 - (&gamma * h).mapv(f64::exp));

    //let beta = (&tss.slice(s![0, ..]) - &tss.slice(s![1, ..]) * (&gamma * h).mapv(f64::exp).into_shape((1, gamma.len())).unwrap()) // / (1.0 - (&gamma * h).mapv(f64::exp));

    // let t_exact = (&gamma * &zmes).mapv(f64::exp) * &alpha + &beta;

    (zmes_result.0, t_res, h_res,)

}

// python API

#[pyfunction]
fn call_homogeneous(tf: f64, tss: Vec<f64>, hss: Vec<f64>, n: usize, t0: Vec<f64>, h0: Vec<f64>, tol: f64) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    // Convert the input vectors to ndarray arrays
    let tss = Array2::from_shape_vec((1, tss.len()), tss).map_err(|e| PyErr::new::<exceptions::PyValueError, _>(format!("{}", e)))?;
    let hss = Array2::from_shape_vec((1, hss.len()), hss).map_err(|e| PyErr::new::<exceptions::PyValueError, _>(format!("{}", e)))?;
    let h0 = Array1::from(h0);

    // Call the homogeneous function
    let (zmes, t_res, h_res) = homogeneous(tf, tss, hss, 1.0, n, t0.into(), h0, tol);

    // Convert the output arrays to vectors and return them
    Ok((zmes.to_vec(), t_res.into_raw_vec(), h_res.into_raw_vec()))
}



#[pymodule]
fn function_conv(_py: Python, m: &PyModule) -> PyResult<()> {
     m.add_function(wrap_pyfunction!(call_homogeneous, m)?)?;
    Ok(())
}
