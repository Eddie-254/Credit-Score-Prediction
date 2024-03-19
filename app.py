import streamlit as st
import joblib
import numpy as np
import sqlite3
import pandas as pd

# Load the trained model
model = joblib.load('Loan_status.pkl')

# Create SQLite connection and cursor
conn = sqlite3.connect('loan_applications.db')
c = conn.cursor()

# Create table if not exists
c.execute('''CREATE TABLE IF NOT EXISTS loan_applications
             (first_name TEXT, middle_name TEXT, surname TEXT, address TEXT, telephone TEXT, email TEXT, 
              gender TEXT, married TEXT, dependents INTEGER, education TEXT, employed TEXT, 
              annual_income REAL, co_income REAL, loan_amount REAL, loan_amount_term INTEGER, 
              credit_history INTEGER, property_area TEXT, loan_status TEXT)''')

# Define the Streamlit app
def main():
    st.title('Loan Prediction App')

    # Create a dictionary to store user inputs in session state
    if 'user_inputs' not in st.session_state:
        st.session_state.user_inputs = {}

    # Form to collect user inputs
    with st.form(key='loan_form'):
        st.subheader('Applicant Details')

        # Input fields for applicant details
        st.text_input('First Name', key='first_name')
        st.text_input('Middle Name', key='middle_name')
        st.text_input('Surname', key='surname')
        st.text_input('Address', key='address')
        st.text_input('Telephone Number', key='telephone')
        st.text_input('Email (Optional)', key='email')

        st.subheader('Loan Application Details')

        # Input fields for loan application details
        gender = st.selectbox('Gender', ['Male', 'Female'], index=0, key='gender')
        married = st.selectbox('Marital Status', ['Married', 'Single'], index=0, key='married')
        dependents = st.number_input('Number of Dependents', min_value=0, step=1, key='dependents')
        education = st.selectbox('Education', ['Graduate', 'Not Graduate'], index=0, key='education')
        employed = st.selectbox('Self Employed', ['Yes', 'No'], index=0, key='employed')
        annual_income = st.number_input('Applicant Income', min_value=0, key='annual_income')
        co_income = st.number_input('Coapplicant Income', min_value=0, key='co_income')
        loan_amount = st.number_input('Loan Amount', min_value=0, key='loan_amount')
        loan_amount_term = st.number_input('Loan Amount Term(Months)', min_value=0, key='loan_amount_term')
        credit_history = st.number_input('Credit History(1-Yes/0-No)', min_value=0, max_value=1, key='credit_history')
        property_area = st.selectbox('Property Area', ['Rural', 'Semiurban', 'Urban'], index=0, key='property_area')

        # Submit button
        submit_button = st.form_submit_button(label='Submit')

    # Clear button
    if st.button('Clear Form'):
        # Clear session state variables related to form inputs
        st.session_state.user_inputs = {key: None for key in st.session_state.user_inputs.keys() if key != 'loan_details'}

    # Process form submission
    if submit_button:
        # Validate mandatory fields
        mandatory_fields = [gender, married, education, employed, annual_income, co_income, loan_amount,
                            loan_amount_term, property_area]
        if all(mandatory_fields):
            # Store user inputs in session state
            st.session_state.user_inputs['first_name'] = st.session_state.first_name
            st.session_state.user_inputs['middle_name'] = st.session_state.middle_name
            st.session_state.user_inputs['surname'] = st.session_state.surname
            st.session_state.user_inputs['address'] = st.session_state.address
            st.session_state.user_inputs['telephone'] = st.session_state.telephone
            st.session_state.user_inputs['email'] = st.session_state.email
            
            st.session_state.user_inputs['loan_details'] = {
                'gender': gender,
                'married': married,
                'dependents': dependents,
                'education': education,
                'employed': employed,
                'annual_income': annual_income,
                'co_income': co_income,
                'loan_amount': loan_amount,
                'loan_amount_term': loan_amount_term,
                'credit_history': credit_history,
                'property_area': property_area
            }

            # Initialize result_message with an empty string
            result_message = ""

            # Predict loan status
            try:
                x_app = np.array([[1 if gender == 'Male' else 0,
                                1 if married == 'Married' else 0,
                                dependents,
                                1 if education == 'Graduate' else 0,
                                1 if employed == 'Yes' else 0,
                                annual_income,
                                co_income,
                                loan_amount,
                                loan_amount_term,
                                credit_history,
                                ['Rural', 'Semiurban', 'Urban'].index(property_area)]])
                prediction = model.predict(x_app)
                result_message = "Congratulations! You are eligible for this loan." if prediction == 1 \
                    else "We're sorry, you are not eligible for this loan."
                st.success(result_message)

                # Save applicant details to database
                c.execute('''INSERT INTO loan_applications (first_name, middle_name, surname, address, telephone, email, gender, married, dependents, education, employed, annual_income, co_income, loan_amount, loan_amount_term, credit_history, property_area, loan_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (st.session_state.user_inputs.get('first_name', ''),
                        st.session_state.user_inputs.get('middle_name', ''),
                        st.session_state.user_inputs.get('surname', ''),
                        st.session_state.user_inputs.get('address', ''),  # Insert address
                        st.session_state.user_inputs.get('telephone', ''),  # Insert telephone number
                        st.session_state.user_inputs.get('email', ''),  # Insert email
                        gender,
                        married,
                        dependents,
                        education,
                        employed,
                        annual_income,
                        co_income,
                        loan_amount,
                        loan_amount_term,
                        credit_history,
                        property_area,
                        'Eligible' if prediction == 1 else 'Declined'))  # Set loan_status based on eligibility

                conn.commit()
            except ValueError:
                st.error("An error occurred while processing the loan application. Please try again.")
        else:
            # If mandatory fields are missing, show an error message
            st.error("Please fill in all mandatory fields except Number of Dependents and Credit History.")


    # Button to view applicants and their status
    if st.button('View Applicants and Status'):
        # Query database for loan applications and status
        c.execute('''SELECT * FROM loan_applications''')
        rows = c.fetchall()
        # Display the applicants and status
        st.write(pd.DataFrame(rows, columns=[i[0] for i in c.description]))

    
if __name__ == '__main__':
    main()
