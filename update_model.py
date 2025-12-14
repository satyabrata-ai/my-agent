#!/usr/bin/env python3
"""
Quick script to update the AGENT_MODEL in .env file
"""

import os
from pathlib import Path


def update_model_in_env(model_name: str):
    """Update or add AGENT_MODEL in .env file"""
    
    env_file = Path(__file__).parent / '.env'
    
    if not env_file.exists():
        print(f"❌ .env file not found at: {env_file}")
        print(f"   Creating new .env file...")
        with open(env_file, 'w') as f:
            f.write(f"AGENT_MODEL={model_name}\n")
        print(f"✅ Created .env with AGENT_MODEL={model_name}")
        return
    
    # Read existing .env
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Check if AGENT_MODEL exists
    model_found = False
    new_lines = []
    
    for line in lines:
        if line.strip().startswith('AGENT_MODEL='):
            new_lines.append(f'AGENT_MODEL={model_name}\n')
            model_found = True
            print(f"✅ Updated AGENT_MODEL to: {model_name}")
        else:
            new_lines.append(line)
    
    # If AGENT_MODEL doesn't exist, add it
    if not model_found:
        new_lines.append(f'\n# Model Configuration\nAGENT_MODEL={model_name}\n')
        print(f"✅ Added AGENT_MODEL={model_name} to .env")
    
    # Write back
    with open(env_file, 'w') as f:
        f.writelines(new_lines)
    
    print(f"📝 .env file updated successfully!")
    print(f"\n🔄 Please restart the agent for changes to take effect.")


def main():
    """Main function"""
    print("🤖 Agent Model Configuration Updater")
    print("=" * 50)
    
    # Available models
    models = {
        "1": ("gemini-2.0-flash-exp", "Fast, default model"),
        "2": ("gemini-3-pro-preview", "Latest, most capable (PREVIEW)"),
        "3": ("gemini-1.5-pro", "Stable production model"),
        "4": ("gemini-1.5-flash", "Fast, lightweight model"),
    }
    
    print("\nAvailable Models:")
    for key, (model, desc) in models.items():
        print(f"  {key}. {model}")
        print(f"     └─ {desc}")
    
    print("\n  5. Custom model name")
    print("  0. Exit")
    
    choice = input("\nSelect model (1-5, or 0 to exit): ").strip()
    
    if choice == "0":
        print("👋 Exiting...")
        return
    
    if choice in models:
        model_name = models[choice][0]
        update_model_in_env(model_name)
    elif choice == "5":
        model_name = input("Enter custom model name: ").strip()
        if model_name:
            update_model_in_env(model_name)
        else:
            print("❌ Model name cannot be empty")
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
