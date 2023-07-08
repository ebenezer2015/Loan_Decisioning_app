
    
import streamlit as st
import pandas as pd
import numpy as np


def update_dataframe(provider, amount, initial_rate, paymentsperyear, years,product_fees, initial_fixed_period, follow_on_rate, cashback, df):
    new_row = [{
        'provider': provider,
        'amount': amount,
        'initial_rate': initial_rate,
        'paymentsperyear': paymentsperyear,
        'years': years,
        'product_fees': product_fees,
        'initial_fixed_period': initial_fixed_period,
        'follow_on_rate': follow_on_rate,
        'cashback': cashback
    }]
    
   

    df = df.append(new_row, ignore_index=True)

    return df

#convert collected dataframe to list
def convert_table_to_format(df):
    converted_data = []
    for _, row in df.iterrows():
        provider = row['provider']
        amount = row['amount']
        initial_rate = row['initial_rate']
        paymentsperyear = row['paymentsperyear']
        years = row['years']
        product_fees = row['product_fees']
        initial_fixed_period = row['initial_fixed_period']
        follow_on_rate = row['follow_on_rate']
        cashback = row['cashback']

        converted_data.append({
            'provider': provider,
            'amount': amount,
            'initial_rate': initial_rate,
            'paymentsperyear': paymentsperyear,
            'years': years,
            'product_fees': product_fees,
            'initial_fixed_period': initial_fixed_period,
            'follow_on_rate': follow_on_rate,
            'cashback' : cashback
        })

    return converted_data

def optmised_schedule(provider, amount, initial_rate, paymentsperyear, years ,product_fees, initial_fixed_period, follow_on_rate, cashback):  
    def PMT(int_rate, no_instalment,loan_amount):
        if int_rate!=0:
            pmt = (int_rate*(loan_amount*(1 + int_rate)**no_instalment))/((1)*(1-(1+ int_rate)**no_instalment))
        else:
            pmt = (-1*(loan_amount)/no_instalment)  
        return(round(pmt,2))
    

    def IPMT(int_rate, per, no_instalment,loan_amount):
        ipmt = -( ((1+int_rate)**(per-1)) * (loan_amount*int_rate + PMT(int_rate, no_instalment,loan_amount)) - PMT(int_rate, no_instalment,loan_amount))
        return(round(ipmt,2))
      

    def PPMT(int_rate, per, no_instalment,loan_amount):
        ppmt = PMT(int_rate, no_instalment,loan_amount) - IPMT(int_rate, per, no_instalment, loan_amount)
        return(round(ppmt,2))
    
    def get_months(start_date):
        date_rng = pd.date_range(start=start_date, periods=paymentsperyear * years, freq='MS')
        return [date.strftime('%Y-%m') for date in date_rng]

    
    annual_interest_rate = initial_rate/100
    df = pd.DataFrame({'Principal' :[PPMT(annual_interest_rate/paymentsperyear, i+1, paymentsperyear*years, amount) for i in range(paymentsperyear*years)],
                        'Interest' :[IPMT(annual_interest_rate/paymentsperyear, i+1, paymentsperyear*years, amount) for i in range(paymentsperyear*years)]})
    df['Instalment'] = df.Principal + df.Interest
    df['Balance'] = amount + np.cumsum(df.Principal)
    df['Total_Interest_Paid'] = np.cumsum(df.Interest)
    df['Total_Principal_Paid'] = np.cumsum(df.Principal)
    df['Total_Instalment_Paid'] = np.cumsum(df.Instalment)
    df['Product_Fees'] = product_fees
    df['Loan'] = amount
    df['Interest_Rate'] = initial_rate
    df['fixed_period'] = initial_fixed_period
    df['Provider'] = provider
    df0 = df.iloc[:,2:].head(2*paymentsperyear).tail(1).reset_index().drop(['index'], axis=1)
    df0['Cashback'] = cashback
    df0['Total_Cost'] = df0['Total_Interest_Paid'] + df0['Product_Fees'] + df0['Cashback']
    df0['Equity'] = round(df0['Total_Principal_Paid']*-1 / df0['Loan'] * 100, 2)
    df0 = df0[['Loan', 'Interest_Rate', 'Instalment', 'Balance', 'Equity', 'Total_Interest_Paid', 'Total_Principal_Paid', 'Total_Instalment_Paid', 'Product_Fees', 'Total_Cost','Cashback']]


 
    ### Case when neither initial fixed period nor follow on rate is supplied """
    if initial_fixed_period == 0 and follow_on_rate == 0:
        return df0
    
    ### Case when one of either initial fixed period and follow on rate is supplied """
    elif (initial_fixed_period == 0 and follow_on_rate != 0) or (initial_fixed_period != 0 and follow_on_rate == 0):
        return f"One of these is missing, either the follow on rate or the initial fixed period?"
    
    ### Case when both initial fixed period and follow on rate are supplied 
    elif initial_fixed_period != 0 and follow_on_rate != 0 :
        follow_on_year = years - initial_fixed_period
        follow_rate = follow_on_rate/100
        df1 = df.head(initial_fixed_period*paymentsperyear)
        bal = df1.tail(1)['Balance'].to_numpy()[0]
        df2 = pd.DataFrame({'Principal' :[PPMT(follow_rate/paymentsperyear, i+1, paymentsperyear*follow_on_year, bal) for i in range(paymentsperyear*follow_on_year)],
                            'Interest' :[IPMT(follow_rate/paymentsperyear, i+1, paymentsperyear*follow_on_year, bal) for i in range(paymentsperyear*follow_on_year)]})

        df2['Instalment'] = df2.Principal + df2.Interest
        df2['Balance'] = bal + np.cumsum(df2.Principal)
        df3 = pd.concat([df1,df2]).reset_index().iloc[:,1:]
        df3['Total_Interest_Paid'] = np.cumsum(df3.Interest)
        df3['Total_Principal_Paid'] = np.cumsum(df3.Principal)
        df3['Total_Instalment_Paid'] = np.cumsum(df3.Instalment)
        df3['Product_Fees'] = product_fees*-1
        df3['Loan'] = amount
        df3['Interest_Rate'] = initial_rate
        df3['Fixed_Period'] = initial_fixed_period
        df3['Provider'] = provider
        df4 = df3.iloc[:,2:].head(initial_fixed_period*paymentsperyear).tail(1).reset_index().drop(['index'], axis=1)
        df4['Cashback'] = cashback
        df4['Total_Cost'] = df4['Total_Interest_Paid'] + df4['Product_Fees'] + df4['Cashback']
        df4['Equity'] = round(df4['Total_Principal_Paid']*-1 / df4['Loan'] * 100, 2)
        df4['Yearly_Avg_Cost']=round(df4['Total_Cost']/df4['Fixed_Period'],2)
        df5 = df4.loc[:,['Provider','Loan','Interest_Rate','Instalment','Balance', 'Equity','Total_Interest_Paid','Total_Principal_Paid','Total_Instalment_Paid','Cashback', 'Product_Fees','Total_Cost','Fixed_Period','Yearly_Avg_Cost']]
        
        
        
        return df5

   

def main():
    
    # Add title and icon
    st.title("Loan Decisioning System")
    
    
 
    st.sidebar.title("Loan Terms")
    provider = st.sidebar.text_input("Loan Provider", value='')
    amount = st.sidebar.number_input("Amount", value=0.0, step=1.0)
    initial_rate = st.sidebar.number_input("Initial Rate", value=0.0)
    paymentsperyear = st.sidebar.number_input("Numbers Of Payments Per Year", value=12)
    years = st.sidebar.number_input("Years of Repayment", value=0, step=1)
    product_fees = st.sidebar.number_input("Product Fees", value=0.0, step=1.0)
    initial_fixed_period = st.sidebar.number_input("Initial Fixed Period", value=0)
    follow_on_rate = st.sidebar.number_input("Follow On Rate", value=0.0, step=1.0)
    cashback = st.sidebar.number_input("Cash Back", value=0.0, step=1.0)
    
    # style
    th_props = [('font-size', '14px'),
                  ('text-align', 'center'),
                  ('font-weight', 'bold'),
                  ('color', '#6d6d6d'),
                  ('background-color', '#f7ffff')]

    td_props = [('font-size', '14px')]

    styles = [
          dict(selector="th", props=th_props),
          dict(selector="td", props=td_props)
          ]
    
    
    st.markdown("This **Loan Decisioning System** allows you to enter loan details and analyze multiple loan products.")
    
    st.markdown("To use the app, enter the loan details on the sidebar, while the '**Update Table**' let the app user to add the data input into the table, the '**Show Input Table**' button allows the user to see the updated tables.")

   
    st.markdown("The '**Get Result**' button displays the final analysis of the products ranking them in order. ")
    

    st.markdown ("The '**Reset**' button reset all the Loan Terms entry back to default. ")
    
    container_1 = st.container()
    container_2 = st.container()
    


    if 'dataframe' not in st.session_state:
        # Create an empty DataFrame if it doesn't exist in session state
        st.session_state.dataframe = pd.DataFrame(columns=['provider', 'amount','initial_rate','paymentsperyear','years','product_fees','initial_fixed_period', 'follow_on_rate','cashback']) 

    if st.sidebar.button("Update Table"):
        st.session_state.dataframe = update_dataframe(provider, amount, initial_rate, paymentsperyear, years, product_fees, initial_fixed_period, follow_on_rate, cashback, st.session_state.dataframe) 
        
    if st.sidebar.button("Show Input Data"):
        with st.container():
            st.header("Input Data")
            st.dataframe(st.session_state.dataframe.drop_duplicates())
       
    if st.sidebar.button("Get Result"):
        
        result = pd.DataFrame()  # Initialize an empty DataFrame to store results
        for params in convert_table_to_format(st.session_state.dataframe):
            provider = params['provider']
            amount = params['amount']
            initial_rate = params['initial_rate']
            paymentsperyear = params['paymentsperyear']
            years = params['years']
            product_fees = params['product_fees']
            initial_fixed_period = params['initial_fixed_period']
            follow_on_rate = params['follow_on_rate']
            cashback = params['cashback']
            result = result.append(optmised_schedule(provider, amount, initial_rate, paymentsperyear, years, product_fees, initial_fixed_period, follow_on_rate, cashback), ignore_index=True) #
            
            # table
        if 'Yearly_Avg_Cost' in result.columns:
            result = result.sort_values('Yearly_Avg_Cost', ascending=False)
            result.reset_index(drop=True, inplace=True)
            
        
        with container_1:
            st.header("Loan Product Table")
            #st.text("This table displays the loan details entered by the user.")
            st.markdown("This table displays the loan details entered by the user.")
            st.table(st.session_state.dataframe.drop_duplicates().style.set_properties(**{'text-align': 'left'}).set_table_styles(styles).format(precision=2))
        
        with container_2:
            st.header("Loan Decisioning Table")
            st.markdown("This table shows the optimized loan decisioning results.")
            st.markdown("Click the '**Get Result**' button to generate the table.")
     
            #st.text("Click 'Get Result' to generate the table.")
            st.table(result.drop_duplicates().style.set_properties(**{'text-align': 'left'}).set_table_styles(styles).format(precision=2))
        
    
    if st.sidebar.button("Reset"):
        # Clear the inputted data and reset the DataFrame
        provider = ''
        amount = 0
        initial_rate = 0
        paymentsperyear = 12
        years = 0
        product_fees = 0
        initial_fixed_period = 0
        follow_on_rate = 0
        cashback = 0
        st.session_state.dataframe = pd.DataFrame(columns=['provider', 'amount','initial_rate','paymentsperyear','years','product_fees','initial_fixed_period','follow_on_rate','cashback']) #

    
    
            #st.dataframe(st.session_state.dataframe)

if __name__ == "__main__":
    main()

    


