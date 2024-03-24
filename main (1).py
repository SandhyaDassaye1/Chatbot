import os
import json
import time
import random
import copy
import requests
import streamlit as st
import openai

from PIL import Image

# Set the Streamlit page configs
st.set_page_config(
    page_title='AI for SWE Mock Interview Questions From Job Descriptions',
    page_icon="👨‍💻"                
)

# Set the OpenAI API key and endpoint
openai.api_key = os.getenv('api key')
openai.api_base = "base url"

# Define constants
general_question_types = ["Multiple Choice", "Open Ended"]
question_types = general_question_types + ["Data Structure and Algorithms", "Behavioral"]


class Prompt:
    def __init__(self, job_description, job_position):
        self.job_description = job_description
        self.job_position = job_position
        self.previous_questions = []

    def add_question(self, question):
        self.previous_questions.append(question)

    def get_template(self):
        if len(self.previous_questions) > 0:
            questions = f"\nQuestion: ".join(self.previous_questions[-3:])
            question_prompt = f"Here are the previous questions:\n{questions}"
        else:
            question_prompt = ""

        return f"""
            [INST]
            <<SYS>>
            %s

            {question_prompt}

            Here is the Job Description:
            {self.job_description}

            Here is the Job Position:
            {self.job_position}
             

            Only respond with your interview question, do not respond with anything other than the interview question you generate.
            <</SYS>>
            [/INST]
        """.strip()

    def get_prompt_for_general_question(self, question_type):
        prompt = f"""
            You are a software engineering interviewing bot, your role is to generate interview questions for the given job description and job title.
            
            You must follow these instructions:
            - First you must analyze the job description and the job position and determine what would be a challenging interview question for this role
            - Generate an interview question that would vet the candidate based on their problem solving abilities and general domain knowledge
            - Your question MUST be a "{question_type}" question! Please format your questions as a "{question_type}" question.
            - If you are given previous questions please think of a unique question not related to the previous questions.
            - Keep the question brief and concise
            - Only respond with the interview question, do not respond with any explanation ONLY respond with the interview question.

        """.strip()
        template = self.get_template()

        return self.get_template() % prompt 

    def get_prompt_for_behavioral_question(self, question_type):
        prompt = f"""
            You are a software engineering interviewing bot, your role is to generate behavioral interview questions for the given job description and job title.
            
            You must follow these instructions:
            - First you must analyze the job description and the job position and determine what would be a good behavioral interview question for this role
            - Think of a behavioral question that would vet whether or not the candidate would either work well in a team, be a dependable engineer, have quality communication and other behavioral things.
            - If you are given previous questions please think of a unique question not related to the previous questions given.
            - Keep the question brief and concise
            - Only respond with the interview question, do not respond with any explanation ONLY respond with the interview question.
        """.strip()
        template = self.get_template()

        return self.get_template() % prompt 

    def get_prompt_for_algorithm_question(self, question_type):
        prompt = f"""
            You are a software engineering interviewing bot, your role is to generate Data Structure and Algorithm interview questions for the given job description and job title.
            
            You must follow these instructions:
            - First you must analyze the job description and the job position and determine what would be a good Data Structure and Algorithm interview question for this role
            - You must present a problem for the candidate to solve that would test the candidates general Computer Science knowledge and competence with Data Structure and Algorithms.
            - Also, use the job description to pick whick programming language you believe would be appropriate to write the problem code in
            - For the problem you generate for the candidate: explain what the constraints are and what time complexity the candidate must respond with.
            - Explain a possible use case for the problem that you think of after generating the problem.
            - If you are given previous questions please think of a unique question not related to the previous questions given.
            - Only respond with the interview problem, do not respond with any explanation ONLY respond with the interview problem.
        """.strip()
        template = self.get_template()

        return self.get_template() % prompt 

    def get_prompt_for_answering_question(self, question, is_algo=False):
        prompt = f"""
            [INST]
            <<SYS>>
            You are a senior software engineer bot, your role is to provide an answer to software engineering interview questions given an interview question.
            
            You must follow these instructions:
            {"" if is_algo else "- You must determine whether the given question is multiple choice or open ended."}
            {"-The question you will be given will be a data structure and algorithm coding problem. Pick a programming language and solve the problem. Write out the full solution and an explanation of how you implemented it." if is_algo else ""}
            - Respond with an accurate answer and if the question is open ended provide and in-depth reason for why your answer is good
            {"- Write out your answer to this coding problem in one of the following programming languages (python, C, javascript, go, ruby, c# or Java) " if is_algo else ""}
            - Breakdown why your answer would be good as if an engineer had to review your response to prepare for an interview
            - If there are any specific technologies, architectures, design paradigms that you utilize in your answer, provide brief definitions for each of these.

            Here is the interview question you need to answer:
            {question}

            Only respond with the question's answer, do not respond with any introduction or affirmative ONLY respond with the answer.
            <</SYS>>
            [/INST]
        """.strip()

        return prompt 

def openai_request(prompt):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    if completion:
        response_content = completion.choices[0].message.content
        return response_content.strip()

def generate_questions(loading_state, main_container):
   
    st.session_state.questions = []
    questions = []

    prompt = Prompt(st.session_state.job_description, st.session_state.job_position)
    
    main_container.write("")
    with main_container:
        content = main_container.container()
        with content:
            for i in range(0, st.session_state.question_count):
                if len(st.session_state.question_types) == 0:
                    question_type = "Open Ended"
                else:
                    question_type = random.choice(st.session_state.question_types)
                
                if question_type in general_question_types:
                    question_prompt = prompt.get_prompt_for_general_question(question_type)
                elif question_type == "Behavioral":
                    question_prompt = prompt.get_prompt_for_behavioral_question(question_type)
                elif question_type == "Data Structure and Algorithms":
                    question_prompt = prompt.get_prompt_for_algorithm_question(question_type)
                else:
                    question_prompt = ""

                question = openai_request(question_prompt)
                if question is not None:
                    print("Got question", len(question))
                    prompt.add_question(question)
                else:
                    print("Failed to get question")

                is_algo = question_type == "Data Structure and Algorithms"
                answer_prompt = prompt.get_prompt_for_answering_question(question, is_algo=is_algo)
            
                if question_type != "Take home Assessment":
                    answer = openai_request(answer_prompt)
                    if answer is not None:
                        print("Got Answer", len(answer))
                    else:
                        print("Failed to get answer")
                else:
                    answer = None

                question_object = {
                    "question": question,
                    "question_type": question_type,
                }

                if answer:
                    question_object["answer"] = answer

                st.markdown(f"### Question #{i+1}")
                st.markdown(f":orange[Type: {question_object['question_type']}]")
                st.markdown(question_object['question'])
                if 'answer' in question_object:
                    with st.expander(":green[Answer (Spoiler)]"):
                        st.markdown(question_object["answer"])
                st.divider()

    st.session_state.questions = copy.deepcopy(questions)
    print("QUESTIONS", len(st.session_state.questions))
    loading_state.write("")

loading_state = st.empty()
main_container = st.empty()

if 'questions' not in st.session_state or len(st.session_state.questions) == 0:
    with main_container:
        content = main_container.container()
        content.title("👨‍💻  Interview GenAI 👨‍💻")
        content.markdown("### :orange[Generate Mock SWE Interview Questions / Answers From Job Descriptions]")
        st.session_state.questions = []

with st.sidebar:
    st.markdown("## Enter Job Details")
    st.markdown("*Paste the basic info for the job you're applying to*")
    st.session_state.job_position = st.text_input("Job Position", placeholder="Paste your job position here (e.g. Junior Software Engineer)")

    st.session_state.job_description = st.text_area("Job Description", placeholder="Paste your job description text here")

    st.divider()

    st.markdown("## Options")

    st.session_state.question_count = st.slider("Amount of Questions You Want", min_value=1, max_value=20)

    st.session_state.question_types = st.multiselect(
        'What type of questions do you want to generate (randomized per question)',
        question_types,
        question_types[-2:])

    st.divider()

    generate_click = st.button("Generate Interview Questions")
    if generate_click:
        generate_questions(loading_state, main_container)