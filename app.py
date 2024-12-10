import asyncio
import websockets
import RPi.GPIO as GPIO
import time

# GPIO setup
BUZZER_PINS = {
    "0": 14,  # WiringPi 15 -> BCM 14 (existing buzzer)
    "1": 4,   # WiringPi 7 -> BCM 4 (new buzzer 1)
    "2": 15   # WiringPi 16 -> BCM 15 (new buzzer 2 on Physical Pin 10)
}

GPIO.setmode(GPIO.BCM)  # Set mode to BCM

# Set up all buzzer pins
for pin in BUZZER_PINS.values():
    GPIO.setup(pin, GPIO.OUT)

# Create PWM instances for each buzzer
pwm_instances = {key: GPIO.PWM(pin, 2000) for key, pin in BUZZER_PINS.items()}  # Initialize PWM with 2kHz frequency

# WebSocket handler function
async def handle_connection(websocket, path):
    try:
        while True:
            message = await websocket.recv()  # Receive message from the client
            print(f"Received message: {message}")
            
            if message[:2] == "on" and len(message) > 3 and message[3] in BUZZER_PINS:
                buzzer_id = message[3]  # Extract the buzzer ID from the message
                pwm = pwm_instances[buzzer_id]
                pwm.start(50)  # Start PWM with 50% Duty Cycle
                await websocket.send(f"Buzzer {buzzer_id} turned ON")
                print(f"Buzzer {buzzer_id} ON")
                time.sleep(3)  # Keep the buzzer on for 3 seconds
                pwm.stop()  # Stop PWM (turn off the buzzer)
                print(f"Buzzer {buzzer_id} OFF")
                await websocket.send(f"Buzzer {buzzer_id} turned OFF after 3 seconds")
            else:
                await websocket.send("Invalid command")
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # GPIO.cleanup() is not called here
        print("Handler closed")

# Start WebSocket server
async def main():
    try:
        server = await websockets.serve(handle_connection, "0.0.0.0", 8765)
        print("WebSocket server started")
        await server.wait_closed()
    finally:
        for pwm in pwm_instances.values():
            pwm.stop()  # Stop all PWM instances when the program exits
        GPIO.cleanup()  # Clean up GPIO when the program exits
        print("GPIO cleaned up")

# Run the asynchronous server
if __name__ == "__main__":
    asyncio.run(main())
