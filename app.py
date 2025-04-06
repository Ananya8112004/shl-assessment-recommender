import streamlit as st
import pandas as pd
import google.generativeai as genai
from config import GEMINI_API_KEY

# 🔐 Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# ✅ Use correct model and method
model = genai.GenerativeModel(model_name="models/gemini-1.5-pro-latest")

# 📄 Load SHL assessment CSV
df = pd.read_csv("shl_assessments.csv")

# 🧠 Streamlit UI
st.title("🔍 SHL Assessment Recommendation System")
query = st.text_area("Enter job description or query:")

if st.button("Get Recommendations"):
    if query.strip() == "":
        st.warning("Please enter a query.")
    else:
        # 🧠 Ask Gemini to extract skills and duration
        prompt = f"""
        Given this job description: "{query}",
        extract:
        1. Required Skills (comma-separated)
        2. Preferred Duration in minutes (integer)
        Respond as:
        Skills: skill1, skill2, skill3
        Duration: XX
        """

        try:
            response = model.generate_content(prompt)
            gemini_response = response.text
            st.markdown("**Gemini Extracted:**")
            st.code(gemini_response)

            # 🛠️ Extract values
            extracted_skills = []
            duration_limit = 60  # default fallback

            for line in gemini_response.split("\n"):
                if "skills" in line.lower():
                    extracted_skills = [skill.strip().lower() for skill in line.split(":")[-1].split(",")]
                if "duration" in line.lower():
                    digits = ''.join(filter(str.isdigit, line))
                    if digits:
                        duration_limit = int(digits)

            # 🧠 Filter SHL assessments
            def match_score(row):
                skills = row["Skills"].lower().split(";")
                return sum(skill in [s.strip() for s in skills] for skill in extracted_skills)

            filtered_df = df[df["Duration (mins)"] <= duration_limit].copy()
            filtered_df["Match Score"] = filtered_df.apply(match_score, axis=1)
            result = filtered_df.sort_values(by="Match Score", ascending=False).head(10)

            if result.empty:
                st.error("❌ No suitable assessments found.")
            else:
                st.markdown("### 🧠 Top Recommendations")
                st.dataframe(result[[
                    "Assessment Name", "URL", "Duration (mins)",
                    "Test Type", "Remote Testing Support", "Adaptive/IRT Support"
                ]])

        except Exception as e:
            st.error(f"Error: {e}")
