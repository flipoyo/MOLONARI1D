# Building with WordPress

WordPress is a tool that helps us build robust HTML/CSS pages quickly.

There are 2 main components for a WordPress page:
- the 'Page' itself
- the 'Site': content that surrounds the page (header, footer, overall appearance, etc.)

## Logging in as admin

The `/wp-admin` URL is by default blocked for admin connection. Once logged, you should see a black panel on top of the website pages. From there, you can navigate to the Dashboard, edit the site (overall appearance), add a new page or edit the current page.

## Building a page

The page/site editor is intuitive if you know the basics of web architecture. It allows you to add/move/delete blocks like
- text
- header
- image
- gallery (many images)
- groups (`div` to combine other components)

When one element is focused, you can change its style on the right panel, or select the parent element by clicking the left-most button that appears on top of the element.

You can then click publish or save in order to save your changes. The effect is immediate on the website.

## Plugins

WordPress allows for plugins that are very useful for a quick deployment of the website. The ones used by the MOLONARI project are:
- `MathJax-LaTeX`, for equations rendering
- `Page scroll to id`, for a smooth scroll of the page

Those are accessible from `Dashboard > Plugins`.

We can also create custom packages for more precise operations. More details about that in `wordpress_sqlite_plugin.md`.