import time


def get_yes_no(prompt):
    """Helper function to get yes/no input."""
    while True:
        response = input(f"{prompt} (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' or 'n'.")

def timeout_sequence():
    """Handles the Timeout (2 mins delay) logic."""
    print("\n[System]: Timeout (2 mins delay)...")
    time.sleep(1)  # Simulating the delay (shortened for testing)
    print("[System]: Resetting system...")
    return

def eco_points_machine():
    user_total_points = 0

    while True:
        # --- START ---
        print("\n" + "=" * 30)
        print("      Welcome to EcoPoints")
        print("=" * 30)

        # --- Is Storage Full? ---
        is_storage_full = get_yes_no("[Sensor]: Is the storage full?")

        if is_storage_full:
            print("\n[Display]: Sorry, machine is currently full. Please try again later.")
            time.sleep(2)
            continue

            # --- Start Button ---
        input("\n[Display]: Press Enter to Start...")

        # --- Show User QR Code ---
        print("[Display]: Showing QR Code...")

        # --- QR Logic Loop ---
        qr_flow_complete = False
        while not qr_flow_complete:
            # --- Is QR Scanned? ---
            is_qr_scanned = get_yes_no("[Sensor]: Was the QR code scanned?")

            if not is_qr_scanned:
                timeout_sequence()
                qr_flow_complete = "TIMEOUT"  # Flag to break outer loops
                break

            # --- Is QR Valid? ---
            is_qr_valid = get_yes_no("[System]: Is the QR code valid?")

            if not is_qr_valid:
                print("\n[Display]: QR not recognized. Please try again.")
                print("[Action]: Showing QR Code again...")
                # Loops back to "Is QR Scanned?" logic implicitly
            else:
                qr_flow_complete = True

        if qr_flow_complete == "TIMEOUT":
            continue  # Go back to Welcome

        # --- TRANSACTION LOOP  ---
        transacting = True
        while transacting:

            # ---  Ready to accept bottles ---
            print("\n[Display]: The machine is ready to accept bottles.")
            print("[Display]: Please insert bottles in place.")

            # ---  Is door closed? ---
            # Loop until door is closed
            while True:
                is_door_closed = get_yes_no("[Sensor]: Is the door closed?")
                if not is_door_closed:
                    print("\n[Display]: Door Open. Please close the door to proceed.")
                else:
                    break

            # --- Is the platform empty? ---
            is_platform_empty = get_yes_no("[Sensor]: Is the platform empty?")

            if is_platform_empty:
                #  Timeout
                timeout_sequence()
                transacting = False  # Break transaction loop
                break  # Break to outer loop (Welcome)

            # --- Verify Bottles ---
            print("[System]: Verifying bottles...")
            time.sleep(1)

            # --- Are Bottles Valid? ---
            bottles_valid = False
            while not bottles_valid:
                bottles_valid = get_yes_no("[System]: Are the bottles valid?")

                if not bottles_valid:
                    # --- Denied Transaction ---
                    print("\n[Display]: Transaction Denied: Invalid Item Detected.")
                    print("[Display]: Please remove invalid item.")
                    input("[Action]: Press Enter once item is removed...")
                    print("[System]: Re-verifying...")
                else:
                    # Proceed if valid
                    pass

            # --- Calculation & Success Display ---
            # Still sample points
            transaction_points = 10
            user_total_points += transaction_points

            print(f"\n[Display]: Transaction Successful + {transaction_points} Points!")
            print(f"[Display]: Your Total Points : {user_total_points} pts")

            # --- Transact Another? ---
            transact_another = get_yes_no("\n[Input]: Do you want to transact another?")

            if transact_another:
                # Loops back to "The machine is ready to accept bottles"
                continue
            else:
                transacting = False

        # If we exited the transaction loop due to timeout, restart main loop
        if qr_flow_complete == "TIMEOUT":
            continue

        if not transacting and qr_flow_complete != "TIMEOUT":
            # --- Calculate sum total points ---
            print("\n" + "*" * 30)
            print(f"[Display]: Your Total Points : {user_total_points} pts")
            print("*" * 30)

            # --- End Transaction ---
            print("[System]: End Transaction.")
            print("Resetting for next user...\n")
            time.sleep(2)
            # Resets user points for the next person
            user_total_points = 0

        # Run the program


if __name__ == "__main__":
    try:
        eco_points_machine()
    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
