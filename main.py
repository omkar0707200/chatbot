from chains.core_chain import handle_user_query
from dotenv import load_dotenv

def main():
    load_dotenv()
    print("🤖 Welcome to Aarogyaa Bharat Chatbot! Type 'exit' to quit.")
    while True:
        query = input("You: ")
        if query.lower() == "exit":
            print("Bot: Goodbye!")
            break
        response = handle_user_query(query)
        print("Bot:", response)

if __name__ == "__main__":
    main()
