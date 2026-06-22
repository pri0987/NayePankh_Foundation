"""NayePankh Foundation — Volunteer & Donation Management UI."""

from __future__ import annotations

from datetime import date
import base64

import streamlit as st
from PIL import Image

from database import init_db, insert_campaign, insert_donation, insert_volunteer, seed_sample_data
from reports import (
    donations_summary_report,
    export_report_text,
    get_campaigns_df,
    get_dashboard_stats,
    get_donations_df,
    get_filter_options,
    get_volunteers_df,
    save_csv_report,
    volunteers_by_city_report,
)

logo = Image.open("logo.jpeg")

st.set_page_config(
    page_title="NayePankh Foundation Hub",
    page_icon=logo,
    layout="wide",
)

init_db()
seed_sample_data()

CITIES = ["Kanpur", "Ghaziabad", "Delhi", "Lucknow", "Noida"]
ROLES = ["Volunteer", "Coordinator", "Fundraising", "Outreach", "Social Media"]
CATEGORIES = ["Education", "Food", "Health", "Clothing"]
PAYMENT_MODES = ["UPI", "Bank Transfer", "Cash", "Cheque"]


def get_base64_image(image_path):
    with open(image_path, "rb") as img:
        return base64.b64encode(img.read()).decode()


def sidebar_branding() -> None:
    st.sidebar.image("logo.jpeg", use_container_width=True)
    st.sidebar.title("NayePankh Foundation")
    st.sidebar.caption("Badalte Bharat Ki Nayi Tasveer")
    st.sidebar.markdown(
        """
        **UP Govt. Registered NGO**

        • 80G Certified
        • 12A Certified
        • Volunteer Driven
        """
    )


def render_dashboard() -> None:
    st.image("logo.jpeg", width=220)
    stats = get_dashboard_stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active Volunteers", stats["active_volunteers"])
    c2.metric("Active Campaigns", stats["active_campaigns"])
    c3.metric("Total Donations", f"₹{stats['total_amount']:,.0f}")
    c4.metric("80G Eligible Amount", f"₹{stats['amount_with_80g']:,.0f}")

    st.subheader("Campaign Fundraising Progress")
    summary = donations_summary_report()
    if not summary.empty:
        st.dataframe(summary, use_container_width=True, hide_index=True)
    else:
        st.info("No campaign data yet.")



def render_volunteers() -> None:
    bg_image = get_base64_image("volunteer_bg.jpeg")

    st.markdown(
        f"""
        <style>
        .volunteer-banner {{
            background-image: url("data:image/jpeg;base64,{bg_image}");
            background-size: cover;
            background-position: center;
            min-height: 320px;
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 25px;
        }}
        .volunteer-banner-content {{
            text-align: center;
            color: white;
            background: rgba(0,0,0,0.45);
            padding: 20px;
            border-radius: 10px;
        }}
        </style>
        <div class="volunteer-banner">
            <div class="volunteer-banner-content">
                <h1>Volunteer Management</h1>
                <p>NayePankh Foundation</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Volunteers")
    options = get_filter_options()

    f1, f2, f3, f4 = st.columns(4)
    search = f1.text_input("Search", placeholder="Name, email, or city", key="vol_search")
    city = f2.selectbox("City", ["All"] + options["cities"], key="vol_city")
    role = f3.selectbox("Role", ["All"] + options["roles"], key="vol_role")
    status = f4.selectbox("Status", ["All", "Active", "Inactive"], key="vol_status")

    df = get_volunteers_df(city=city, role=role, status=status, search=search)
    st.dataframe(df, use_container_width=True, hide_index=True)

    if st.button("Export Volunteers CSV", key="export_vol"):
        path = save_csv_report(df, "volunteers")
        st.success(f"Saved report to `{path}`")

    with st.expander("Add Volunteer"):
        with st.form("add_volunteer"):
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            city_new = st.selectbox("City", CITIES)
            role_new = st.selectbox("Role", ROLES)
            status_new = st.selectbox("Status", ["Active", "Inactive"])
            joined_on = st.date_input("Joined On", value=date.today())
            if st.form_submit_button("Save Volunteer"):
                if name and email:
                    insert_volunteer(name, email, phone, city_new, role_new, status_new, joined_on)
                    st.success("Volunteer added.")
                    st.rerun()
                else:
                    st.error("Name and email are required.")


def render_campaigns() -> None:
    st.subheader("Campaigns")
    options = get_filter_options()

    f1, f2, f3 = st.columns(3)
    search = f1.text_input("Search", placeholder="Campaign name or city", key="camp_search")
    category = f2.selectbox("Category", ["All"] + options["categories"], key="camp_category")
    city = f3.selectbox("City", ["All"] + options["cities"], key="camp_city")
    status = st.selectbox("Status", ["All", "Active", "Completed", "Paused"], key="camp_status")

    df = get_campaigns_df(category=category, city=city, status=status, search=search)
    st.dataframe(df, use_container_width=True, hide_index=True)

    if st.button("Export Campaigns CSV", key="export_camp"):
        path = save_csv_report(df, "campaigns")
        st.success(f"Saved report to `{path}`")

    with st.expander("Add Campaign"):
        with st.form("add_campaign"):
            name = st.text_input("Campaign Name")
            category_new = st.selectbox("Category", CATEGORIES)
            city_new = st.selectbox("Campaign City", CITIES)
            status_new = st.selectbox("Campaign Status", ["Active", "Completed", "Paused"])
            target = st.number_input("Target Amount (₹)", min_value=0.0, step=1000.0)
            start_date = st.date_input("Start Date", value=date.today())
            has_end_date = st.checkbox("Set end date")
            end_date = st.date_input("End Date", value=date.today(), disabled=not has_end_date)
            if st.form_submit_button("Save Campaign"):
                if name:
                    insert_campaign(
                        name,
                        category_new,
                        city_new,
                        status_new,
                        target,
                        start_date,
                        end_date if has_end_date else None,
                    )
                    st.success("Campaign added.")
                    st.rerun()
                else:
                    st.error("Campaign name is required.")



def render_donations() -> None:

    st.markdown("""
    <style>
    .donation-banner{position:relative;margin-bottom:30px;}
    .donation-overlay{
        position:absolute;top:0;left:0;width:100%;height:350px;
        background:rgba(0,0,0,0.45);border-radius:20px;
    }
    .donation-content{
        position:absolute;top:50%;left:50%;
        transform:translate(-50%,-50%);
        color:white;text-align:center;width:80%;
    }
    .donation-title{font-size:48px;font-weight:700;}
    .donation-subtitle{font-size:20px;}
    </style>
    """, unsafe_allow_html=True)

    banner = get_base64_image("campaign_bg.jpeg")

    st.markdown(f"""
    <div style="position:relative;margin-bottom:30px;">
        <img src="data:image/jpeg;base64,{banner}"
             style="width:100%;height:350px;object-fit:cover;border-radius:20px;">
        <div class="donation-overlay"></div>
        <div class="donation-content">
            <div class="donation-title">❤️ Donation Management</div>
            <div class="donation-subtitle">Every Contribution Creates Impact</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    options = get_filter_options()
    campaign_map = {row["name"]: row["id"] for row in options["campaigns"]}

    all_donations = get_donations_df()

    total_amount = all_donations["amount"].sum() if not all_donations.empty else 0
    total_donors = all_donations["donor_name"].nunique() if not all_donations.empty else 0
    total_donations = len(all_donations)
    avg_donation = round(total_amount / total_donations) if total_donations else 0

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("💰 Total Raised", f"₹{total_amount:,.0f}")
    c2.metric("👥 Donors", total_donors)
    c3.metric("🎁 Donations", total_donations)
    c4.metric("📈 Avg Donation", f"₹{avg_donation:,.0f}")

    st.markdown("## 🔍 Search & Filter Donations")

    f1, f2, f3, f4 = st.columns(4)
    search = f1.text_input("Search", placeholder="Donor name or notes", key="don_search")
    campaign_name = f2.selectbox("Campaign", ["All"] + list(campaign_map.keys()), key="don_campaign")
    payment_mode = f3.selectbox("Payment Mode", ["All"] + PAYMENT_MODES, key="don_payment")
    receipt_only = f4.checkbox("80G receipts only", key="don_80g")

    d1, d2 = st.columns(2)
    date_from = d1.date_input("From date", value=None, key="don_from")
    date_to = d2.date_input("To date", value=None, key="don_to")

    campaign_id = campaign_map.get(campaign_name) if campaign_name != "All" else None

    df = get_donations_df(
        campaign_id=campaign_id,
        payment_mode=payment_mode,
        receipt_only=receipt_only,
        search=search,
        date_from=date_from.isoformat() if date_from else None,
        date_to=date_to.isoformat() if date_to else None,
    )

    total = df["amount"].sum() if not df.empty else 0
    st.success(f"💚 Filtered Donation Total: ₹{total:,.0f}")

    st.dataframe(df, use_container_width=True, hide_index=True)

def render_reports() -> None:
    st.subheader("Reports")
    report_type = st.selectbox(
        "Report Type",
        ["Donations Summary by Campaign", "Volunteers by City", "Full Donations Export"],
    )

    if report_type == "Donations Summary by Campaign":
        df = donations_summary_report()
    elif report_type == "Volunteers by City":
        df = volunteers_by_city_report()
    else:
        df = get_donations_df()

    st.dataframe(df, use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)
    if c1.button("Download CSV"):
        path = save_csv_report(df, report_type.lower().replace(" ", "_"))
        st.success(f"Saved to `{path}`")

    text_report = export_report_text(report_type, df)
    c2.download_button(
        "Download Text Report",
        data=text_report,
        file_name=f"nayepankh_report_{date.today().isoformat()}.txt",
        mime="text/plain",
    )


def main() -> None:
    sidebar_branding()
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Volunteers", "Campaigns", "Donations", "Reports"],
    )

    col1, col2 = st.columns([1, 4])

    with col1:
        st.image("logo.jpeg", width=130)

    with col2:
        st.title("NayePankh Foundation Hub")
        st.caption("Manage volunteers, campaigns, donations, and impact reports.")

    if page == "Dashboard":
        render_dashboard()
    elif page == "Volunteers":
        render_volunteers()
    elif page == "Campaigns":
        render_campaigns()
    elif page == "Donations":
        render_donations()
    else:
        render_reports()


if __name__ == "__main__":
    main()
