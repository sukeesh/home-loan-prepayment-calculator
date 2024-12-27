import streamlit as st
import pandas as pd

def indian_comma_format(amount: float) -> str:
    return f"{amount:,.2f}"

def format_indian_number(num: float) -> str:
    if num >= 1_00_00_000:
        return f"{num / 1_00_00_000:.2f} Cr"
    elif num >= 1_00_000:
        return f"{num / 1_00_000:.2f} L"
    else:
        return indian_comma_format(num)

def calculate_emi(principal, annual_interest_rate, tenure_months):
    monthly_interest_rate = (annual_interest_rate / 100.0) / 12.0
    if monthly_interest_rate == 0:
        return principal / tenure_months
    emi = principal * monthly_interest_rate / (1 - (1 + monthly_interest_rate) ** (-tenure_months))
    return emi

def simulate_loan_mf_scenario(
    loan_principal,
    annual_loan_rate,
    tenure_months,
    house_value,
    house_annual_growth,
    mf_initial_investment,
    mf_monthly_addition,
    mf_annual_growth,
    prepay_month
):
    monthly_house_rate = (1 + house_annual_growth) ** (1/12) - 1
    monthly_mf_rate    = (1 + mf_annual_growth)    ** (1/12) - 1

    emi = calculate_emi(loan_principal, annual_loan_rate, tenure_months)

    current_principal    = loan_principal
    current_house_value  = house_value
    current_mf_value     = mf_initial_investment
    loan_closed_month    = None

    for month in range(1, tenure_months + 1):
        current_house_value *= (1 + monthly_house_rate)

        if loan_closed_month is None:
            current_mf_value += mf_monthly_addition
        else:
            current_mf_value += (emi + mf_monthly_addition)

        if loan_closed_month is None:
            monthly_interest = current_principal * ((annual_loan_rate / 100.0) / 12.0)
            monthly_principal_part = emi - monthly_interest
            current_principal -= monthly_principal_part
            if current_principal < 0:
                current_principal = 0

            if month == prepay_month and current_principal > 0:
                lumpsum = min(current_mf_value, current_principal)
                current_mf_value -= lumpsum
                current_principal -= lumpsum
                if current_principal < 0:
                    current_principal = 0

            if current_principal <= 0 and loan_closed_month is None:
                loan_closed_month = month

        current_mf_value *= (1 + monthly_mf_rate)

    return current_house_value, current_mf_value, loan_closed_month

def main():
    st.title("Loan Prepayment vs. Net Worth Simulation")

    st.markdown("""
    This app allows you to explore how a **one-time** prepayment of your loan principal (using Mutual Funds) 
    in different months can affect your **final net worth** (House + MF) at the end of a chosen tenure.
    """)

    st.sidebar.header("Loan Parameters")
    loan_principal_lakhs = st.sidebar.slider("Loan Principal (Lakhs)", 1.0, 200.0, 50.0, step=1.0)
    annual_interest_rate_loan = st.sidebar.slider("Annual Loan Rate (%)", 0.0, 20.0, 8.0, step=0.5)
    tenure_years = st.sidebar.slider("Tenure (years)", 1, 30, 20, step=1)
    tenure_months = tenure_years * 12

    st.sidebar.header("House Parameters")
    house_value_cr = st.sidebar.slider("House Value (Cr)", 0.5, 10.0, 2.0, step=0.1)
    house_annual_growth = st.sidebar.slider("House Annual Growth (%)", 0.0, 15.0, 5.0, step=0.5)

    st.sidebar.header("Mutual Fund Parameters")
    mf_initial_investment_lakhs = st.sidebar.slider("MF Initial (Lakhs)", 0.0, 500.0, 33.0, step=1.0)
    mf_monthly_addition_lakhs = st.sidebar.slider("MF Monthly Add (Lakhs)", 0.0, 10.0, 2.35, step=0.05)
    mf_annual_growth = st.sidebar.slider("MF Annual Growth (%)", 0.0, 30.0, 14.0, step=0.5)

    loan_principal = loan_principal_lakhs * 1_00_000
    house_value = house_value_cr * 1_00_00_000
    mf_initial_investment = mf_initial_investment_lakhs * 1_00_000
    mf_monthly_addition = mf_monthly_addition_lakhs * 1_00_000

    house_annual_growth_decimal = house_annual_growth / 100.0
    mf_annual_growth_decimal = mf_annual_growth / 100.0

    results = []
    for prepay_month in range(0, tenure_months + 1):
        final_house, final_mf, closed_mth = simulate_loan_mf_scenario(
            loan_principal=loan_principal,
            annual_loan_rate=annual_interest_rate_loan,
            tenure_months=tenure_months,
            house_value=house_value,
            house_annual_growth=house_annual_growth_decimal,
            mf_initial_investment=mf_initial_investment,
            mf_monthly_addition=mf_monthly_addition,
            mf_annual_growth=mf_annual_growth_decimal,
            prepay_month=prepay_month
        )
        net_worth = final_house + final_mf
        results.append({
            "PrepayMonth": prepay_month,
            "HouseValue": final_house,
            "MFValue": final_mf,
            "NetWorth": net_worth
        })

    df = pd.DataFrame(results)

    st.subheader("Simulation Results")
    df_display = df.copy()
    df_display["HouseValue"] = df_display["HouseValue"].apply(format_indian_number)
    df_display["MFValue"] = df_display["MFValue"].apply(format_indian_number)
    df_display["NetWorth"] = df_display["NetWorth"].apply(format_indian_number)

    # Fix: use .style.format() instead of .set_precision()
    df_display_styled = df_display.style.format(precision=2)
    st.dataframe(df_display_styled, height=500)

    st.write("#### How Does the One-Time Prepayment Month Affect Final Net Worth?")
    chart_df = df.set_index("PrepayMonth")[["HouseValue", "MFValue", "NetWorth"]]
    st.line_chart(chart_df)

if __name__ == "__main__":
    main()
