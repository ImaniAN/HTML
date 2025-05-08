import mysql.connector
import logging
from datetime import datetime

class BillingService:
    def __init__(self):
        self.rates = {
            'internet': {
                'per_minute': 0.05,
                'per_hour': 2.50,
                'per_day': 15.00
            },
            'printing': {
                'black_white': 0.10,
                'color': 0.25
            }
        }

        self.db_config = {
             'host': 'localhost',
             'user': 'cafe_admin',
             'password': 'admin@123',
             'cafe_db': 'cafe_db'
        }

        self.test_data = {
            1: {'balance': 100.00, 'name': 'John'},
            2: {'balance': 50, 'name': 'Mike'}
        }

    def get_db_connection(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logging.error(f"Database connection error: {e}")
            return None

    def get_balance(self, user_id):
        try:
            conn = self.get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT credit_balance
                    FROM users
                    WHERE id = %s
                """, (user_id,))
                result = cursor.fetchone()
                cursor.close()
                conn.close()

                if result:
                    return float(result['credit_balance'])
        except Exception as e:
            logging.error(f"Error getting balance: {e}")
            
        return self.test_data.get(user_id, {}).get('balance', 0.00)
        
    def charge_session(self, user_id, duration_minutes):
        try:
            hours = duration_minutes / 60
            if hours >= 24:
                cost = self.rates['internet']['per_day'] * (hours / 24)
            elif hours >= 1:
                cost = self.rates['internet']['per_hour'] * hours
            else:
                cost = self.rates['internet']['per_minute'] * duration_minutes

            conn = self.ge_db_connection()
            if conn:
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE users
                    SET credit_balance = credit_balance - %s
                    WHERE id = %s
                """, (cost, user_id))
                
                cursor.execute("""
                    INSERT INTO billing (
                        user_id,
                        amount,
                        description,
                        transaction_type
                    ) VALUES (%s, %s, %s, %s)
               """, (
                    user_id,
                    cost,
                    f'INternet session: {duration_minutes} minutes',
                    'charge'
               ))

                conn.commit()
                cursor.close()
                conn.close()
            else:
                if user_id in self.test_data:
                    self.test_data[user_id]['balance'] -= cost
            return cost

        except Exception as e:
            logging.error(f"Charge calculation error: {e}")
            return None

    def get_transaction_history(self, user_id):
        try:
            conn = self.get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT * FROM billing
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT 10
                """, (user_id,))

                transactions = cursor.fetchall()
                cursor.close()
                conn.close()
                return transactions

            return [
                {
                    'amount': 10.00,
                    'description': 'Test transaction 1',
                    'transaction_type': 'deposit',
                    'created_at': datetime.now()
                }
            ]

        except Exception as e:
            logging.error(f"Transaction history error: {e}")
            return []
