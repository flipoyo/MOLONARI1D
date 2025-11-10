import json
import unittest
from src.receiver.adapt_nodered_mqtt import init_db

class TestConfig(unittest.TestCase):
    def setUp(self):
        with open('src/receiver/config.json') as config_file:
            self.config = json.load(config_file)

    def test_config_values(self):
        self.assertIn('MQTT_BROKER', self.config)
        self.assertIn('MQTT_PORT', self.config)
        self.assertIn('DB_FILENAME', self.config)

    def test_database_initialization(self):
        db_conn = init_db(self.config['DB_FILENAME'])
        self.assertIsNotNone(db_conn)
        db_conn.close()

if __name__ == '__main__':
    unittest.main()