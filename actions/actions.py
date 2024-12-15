from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet
import random
import sqlite3
from sqlite3 import Error
import os

def create_connection():
    """Create a database connection to the SQLite database"""
    conn = None
    try:
        conn = sqlite3.connect('foodbot.db')
        return conn
    except Error as e:
        print(f"Error connecting to database: {e}")
    return conn

def create_tables():
    """Create the necessary tables if they don't exist"""
    conn = create_connection()
    if conn is not None:
        try:
            c = conn.cursor()
            
            # Create customers table
            c.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    sender_id TEXT PRIMARY KEY,
                    mobile_number TEXT,
                    verification_pin TEXT,
                    address TEXT
                )
            ''')
            
            # Create orders table
            c.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    sender_id TEXT,
                    item TEXT,
                    status TEXT DEFAULT 'pending',
                    FOREIGN KEY (sender_id) REFERENCES customers (sender_id)
                )
            ''')

            c.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT,
                    feedback_text TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders (order_id)
                )
            ''')

            conn.commit()
        except Error as e:
            print(f"Error creating tables: {e}")
        finally:
            conn.close()

# Initialize database tables
create_tables() 

class ActionGreet(Action):
    def name(self) -> Text:
        return "action_greet"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        buttons = [
            {"payload": "/show_menu", "title": "Show Menu"},
            {"payload": "/track_order", "title": "Track Order"},
            {"payload": "/give_feedback", "title": "Give Feedback"}
        ]
        print(f"Input message: {tracker.latest_message.get('text')}")
        print(f"Sender ID: {tracker.sender_id}")
        dispatcher.utter_message(
            text="Welcome to FoodBot! How can I help you today?",
            buttons=buttons
        )
        return []

class ActionShowMenu(Action):
    def name(self) -> Text:
        return "action_show_menu"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        buttons = [
            {"payload": "Combo 1 - $10", "title": "Combo 1 - $10"},
            {"payload": "Combo 2 - $12", "title": "Combo 2 - $12"},
            {"payload": "Combo 3 - $15", "title": "Combo 3 - $15"},
            {"payload": "Combo 4 - $18", "title": "Combo 4 - $18"}
        ]
        print(f"Input message: {tracker.latest_message.get('text')}")
        print(f"Sender ID: {tracker.sender_id}")
        dispatcher.utter_message(
            text="Here are our available combos:",
            buttons=buttons
        )
        return []

class ActionOrderItem(Action):
    def name(self) -> Text:
        return "action_order_item"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        sender_id = tracker.sender_id
        item = tracker.latest_message.get('text')
        print(f"Input message: {tracker.latest_message.get('text')}")
        print(f"Sender ID: {tracker.sender_id}")
        conn = create_connection()
        if conn is not None:
            try:
                c = conn.cursor()
                
                # Generate random 4-digit order ID
                order_id = str(random.randint(1000, 9999))
                
                # Insert new order
                c.execute('''
                    INSERT INTO orders (order_id, sender_id, item)
                    VALUES (?, ?, ?)
                ''', (order_id, sender_id, item))
                
                conn.commit()
            except Error as e:
                print(f"Database error: {e}")
            finally:
                conn.close()
        return []

class ActionAskContact(Action):
    def name(self) -> Text:
        return "action_ask_contact"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        print(f"Input message: {tracker.latest_message.get('text')}")
        print(f"Sender ID: {tracker.sender_id}")
        dispatcher.utter_message(text="Please provide your 10-digit contact number.")
        return []

class ValidateContactForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_contact_form"

    def validate_contact_number(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        
        print(f"Input message: {tracker.latest_message.get('text')}")
        print(f"Sender ID: {tracker.sender_id}")
        if slot_value.isdigit() and len(slot_value) == 10:
            return {"contact_number": slot_value}
        else:
            dispatcher.utter_message(text="Please provide a valid 10-digit contact number.")
            return {"contact_number": None}

class ActionSendPin(Action):
    def name(self) -> Text:
        return "action_send_pin"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        sender_id = tracker.sender_id

        print(f"Input message: {tracker.latest_message.get('text')}")
        print(f"Sender ID: {tracker.sender_id}")
        mobile_number = tracker.get_slot("contact_number")
        pin = str(random.randint(0000, 9999)).zfill(4)
        
        conn = create_connection()
        if conn is not None:
            try:
                c = conn.cursor()
                
                c.execute('''
                    INSERT INTO customers (sender_id, mobile_number, verification_pin)
                    VALUES (?, ?, ?)
                    ON CONFLICT(sender_id) 
                    DO UPDATE SET mobile_number=?, verification_pin=?
                ''', (sender_id, mobile_number, pin, mobile_number, pin))
                
                conn.commit()
            except Error as e:
                print(f"Database error: {e}")
            finally:
                conn.close()

        dispatcher.utter_message(
            text=f"Your verification PIN is {pin}. Please enter it to continue."
        )
        return []

class ActionValidatePin(Action):
    def name(self) -> Text:
        return "action_validate_pin"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        sender_id = tracker.sender_id
        entered_pin = tracker.latest_message.get('text')
        
        conn = create_connection()
        if conn is not None:
            try:
                c = conn.cursor()
                
                c.execute('''
                    SELECT verification_pin 
                    FROM customers 
                    WHERE sender_id = ?
                ''', (sender_id,))
                
                result = c.fetchone()
                if result and result[0] == entered_pin:
                    return []  # Success, will trigger action_ask_address
                else:
                    dispatcher.utter_message(
                        text="Invalid PIN. Please try again."
                    )
            except Error as e:
                print(f"Database error: {e}")
            finally:
                conn.close()
        return []

class ActionAskAddress(Action):
    def name(self) -> Text:
        return "action_ask_address"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        print(f"Input message: {tracker.latest_message.get('text')}")
        print(f"Sender ID: {tracker.sender_id}")
        dispatcher.utter_message(text="Please provide your delivery address.")
        return []

class ValidateAddressForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_address_form"

    def validate_address(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        
        print(f"Input message: {tracker.latest_message.get('text')}")
        print(f"Sender ID: {tracker.sender_id}")
        if len(slot_value) > 10:
            return {"address": slot_value}
        else:
            dispatcher.utter_message(text="Please provide a complete address with more details.")
            return {"address": None}

class ActionSaveAddress(Action):
    def name(self) -> Text:
        return "action_save_address"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        sender_id = tracker.sender_id
        address = tracker.get_slot("address")
        
        print(f"Input message: {tracker.latest_message.get('text')}")
        print(f"Sender ID: {tracker.sender_id}")

        conn = create_connection()
        if conn is not None:
            try:
                c = conn.cursor()
                
                c.execute('''
                    UPDATE customers 
                    SET address = ? 
                    WHERE sender_id = ?
                ''', (address, sender_id))
                
                conn.commit()

                buttons = [
                    {"payload": "/order_done", "title": "Make Payment"},
                ]

                dispatcher.utter_message(
                    text="Address saved! Make the payment by clicking on the button",
                    buttons=buttons
                )
            except Error as e:
                print(f"Database error: {e}")
            finally:
                conn.close()
        return []

class ActionOrderDone(Action):
    def name(self) -> Text:
        return "action_order_done"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        sender_id = tracker.sender_id
        
        print(f"Input message: {tracker.latest_message.get('text')}")
        print(f"Sender ID: {tracker.sender_id}")

        conn = create_connection()
        if conn is not None:
            try:
                c = conn.cursor()
                
                # Update order status and get order ID
                c.execute('''
                    SELECT order_id FROM orders 
                    WHERE sender_id = ? AND status = 'pending'
                ''', (sender_id,))
                
                result = c.fetchone()
                if result:
                    order_id = result[0]
                    
                    c.execute('''
                        UPDATE orders 
                        SET status = 'confirmed' 
                        WHERE order_id = ?
                    ''', (order_id,))
                    
                    conn.commit()
                    
                    dispatcher.utter_message(
                        text=f"Your order is confirmed and your order ID is {order_id}. Thank you for ordering!"
                    )
                else:
                    dispatcher.utter_message(
                        text="No pending order found."
                    )
            except Error as e:
                print(f"Database error: {e}")
            finally:
                conn.close()
        return []



class ActionAskOrderIdForTracking(Action):
    def name(self) -> Text:
        return "action_ask_order_id_for_tracking"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Please provide your order ID to track your order.")
        return []
    
class ValidateOrderTrackingForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_order_tracking_form"

    def validate_tracking_order_id(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        # Validate if order exists
        conn = create_connection()
        if conn is not None:
            try:
                c = conn.cursor()
                c.execute('''
                    SELECT order_id 
                    FROM orders 
                    WHERE order_id = ?
                ''', (slot_value,))
                
                result = c.fetchone()
                if result:
                    return {"tracking_order_id": slot_value}
                else:
                    dispatcher.utter_message(text="Sorry, I couldn't find an order with that ID. Please check and try again.")
                    return {"tracking_order_id": None}
            except Error as e:
                print(f"Database error: {e}")
            finally:
                conn.close()
        return {"tracking_order_id": None}

class ActionCheckOrderStatus(Action):
    def name(self) -> Text:
        return "action_check_order_status"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        order_id = tracker.get_slot("tracking_order_id")
        
        conn = create_connection()
        if conn is not None:
            try:
                c = conn.cursor()
                c.execute('''
                    SELECT status 
                    FROM orders 
                    WHERE order_id = ?
                ''', (order_id,))
                
                result = c.fetchone()
                if result:
                    # Add buttons for next actions
                    buttons = [
                        {"payload": "/show_menu", "title": "Show Menu"},
                        {"payload": "/track_order", "title": "Track Order"},
                        {"payload": "/give_feedback", "title": "Give Feedback"}
                    ]
                    
                    dispatcher.utter_message(
                        text=f"Your order #{order_id} status is: {result[0]}",
                        buttons=buttons
                    )
                else:
                    dispatcher.utter_message(
                        text="Sorry, I couldn't find an order with that ID. Please check and try again."
                    )
                    
            except Error as e:
                print(f"Database error: {e}")
            finally:
                conn.close()
        
        # Always clear the tracking_order_id slot after checking
        return [SlotSet("tracking_order_id", None)]



class ActionAskOrderIdForFeedback(Action):
    def name(self) -> Text:
        return "action_ask_order_id_for_feedback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Please provide your order ID to give feedback.")
        return []

class ValidateFeedbackForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_feedback_form"

    def validate_feedback_order_id(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        # Validate if order exists
        conn = create_connection()
        if conn is not None:
            try:
                c = conn.cursor()
                c.execute('''
                    SELECT order_id 
                    FROM orders 
                    WHERE order_id = ?
                ''', (slot_value,))
                
                result = c.fetchone()
                if result:
                    # Add this line to prompt for feedback after valid order ID
                    dispatcher.utter_message(text="Great! Now please share your feedback about your order.")
                    return {"feedback_order_id": slot_value}
                else:
                    dispatcher.utter_message(text="Sorry, I couldn't find an order with that ID. Please check and try again.")
                    return {"feedback_order_id": None}
            except Error as e:
                print(f"Database error: {e}")
            finally:
                conn.close()
        return {"feedback_order_id": None}

    def validate_feedback_text(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        if len(slot_value.strip()) > 0:
            return {"feedback_text": slot_value}
        else:
            dispatcher.utter_message(text="Please provide some feedback text.")
            return {"feedback_text": None}

class ActionAskFeedback(Action):
    def name(self) -> Text:
        return "action_ask_feedback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Please share your feedback about your order.")
        return []

class ActionSaveFeedback(Action):
    def name(self) -> Text:
        return "action_save_feedback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        order_id = tracker.get_slot("feedback_order_id")
        feedback_text = tracker.get_slot("feedback_text")
        
        conn = create_connection()
        if conn is not None:
            try:
                c = conn.cursor()
                
                c.execute('''
                    INSERT INTO feedback (order_id, feedback_text)
                    VALUES (?, ?)
                ''', (order_id, feedback_text))
                
                conn.commit()
                
                buttons = [
                    {"payload": "/show_menu", "title": "Show Menu"},
                    {"payload": "/track_order", "title": "Track Order"},
                    {"payload": "/give_feedback", "title": "Give Feedback"}
                ]
                
                dispatcher.utter_message(
                    text="Thank you for your feedback! Is there anything else I can help you with?",
                    buttons=buttons
                )
            except Error as e:
                print(f"Database error: {e}")
            finally:
                conn.close()
        
        # Clear the slots after saving feedback
        return [SlotSet("feedback_order_id", None), SlotSet("feedback_text", None)]
