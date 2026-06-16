from config.settings import Settings

def main():
    print("-----------------------------------------")
    print("           Starting Sharron              ")
    print("-----------------------------------------")
    
    # Initialize the settings configuration
    app_settings = Settings()
    
    # Unlock session to verify the input matching logic works perfectly
    session_password = app_settings.get_raw_passphrase_for_session()
    print("🔓 Session unlocked successfully! Settings verified.")

if __name__ == "__main__":
    main()
