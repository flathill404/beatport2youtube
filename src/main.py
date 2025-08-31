from dotenv import load_dotenv

from beatport2youtube import workflow

if __name__ == "__main__":
    load_dotenv()

    workflow.step1()
    workflow.step2()
