import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import platform
import seaborn as sns

from scipy.ndimage import rotate

import preprocessor
import helper

# ----------------- Emoji Font Setup ----------------
def get_emoji_font():
    system = platform.system()
    if system == "Windows":
        return "Segoe UI Emoji"
    elif system == "Darwin":  # macOS
        return "Apple Color Emoji"
    else:  # Linux
        return "Noto Color Emoji"

emoji_font = get_emoji_font()

# ----------------- Streamlit Config ----------------
st.set_page_config(layout="wide")
st.sidebar.title("InsightTalk")

uploaded_file = st.sidebar.file_uploader("Choose a WhatsApp chat .txt file")
if uploaded_file is None:
    st.sidebar.info("Upload a WhatsApp chat .txt file to start the analysis.")
else:
    # --- read file safely ---
    bytes_data = uploaded_file.getvalue()
    try:
        data = bytes_data.decode("utf-8")
    except Exception:
        data = bytes_data.decode("latin-1")  # fallback

    # --- preprocess to dataframe using your preprocessor ---
    df = preprocessor.preprocess(data)

    # ✅ Check if DataFrame is empty
    if df.empty or 'user' not in df.columns:
        st.warning("No valid chat data found in this file. Please upload a proper WhatsApp export (.txt).")
        st.stop()

    # prepare user list for selectbox
    user_list = df['user'].unique().tolist()
    if "group_notification" in user_list:
        user_list.remove('group_notification')
    user_list = sorted(user_list)
    user_list.insert(0, "Overall")

    selected_user = st.sidebar.selectbox("Show Analysis wrt", user_list)

    if st.sidebar.button("Show Analysis"):
        # ---------------- Stats Area ----------------
        try:
            num_messages, words, num_media_messages, num_links = helper.fetch_stats(selected_user, df)
        except Exception as e:
            st.error(f"Error while fetching stats: {e}")
            num_messages = words = num_media_messages = num_links = 0

        st.title("Top Statistics")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.header("Total Messages")
            st.title(num_messages)
        with col2:
            st.header("Total Words")
            st.title(words)
        with col3:
            st.header("Media Shared")
            st.title(num_media_messages)
        with col4:
            st.header("Links Shared")
            st.title(num_links)

        # ----------------- Monthly Timeline -----------------------
        st.title("Monthly Timeline")
        timeline = helper.monthly_timeline(selected_user, df)
        fig, ax = plt.subplots()
        ax.plot(timeline['time'], timeline['message'], color='red')
        plt.xticks(rotation='vertical')
        st.pyplot(fig)

        # ---------------- Daily timeline ----------------------------
        st.title("Daily Timeline")
        daily_timeline = helper.daily_timeline(selected_user, df)
        fig, ax = plt.subplots()
        ax.plot(daily_timeline['only_date'], daily_timeline['message'], color="blue")
        plt.xticks(rotation='vertical')
        st.pyplot(fig)

        # ---------------- Activity Map -----------------------------
        st.title("Activity Map")
        col1, col2 = st.columns(2)

        with col1:
            st.header("Most busy day")
            busy_day = helper.week_activity_map(selected_user, df)
            fig, ax = plt.subplots()
            ax.bar(busy_day.index, busy_day.values)
            plt.xticks(rotation='vertical')
            st.pyplot(fig)

        with col2:
            st.header("Most busy Month")
            busy_month = helper.month_activity_map(selected_user, df)
            fig, ax = plt.subplots()
            ax.bar(busy_month.index, busy_month.values, color='orange')
            plt.xticks(rotation='vertical')
            st.pyplot(fig)

        # ---------------- Weekly Activity Heat Map ----------------
        st.title("Weekly Activity Map")
        user_heatmap = helper.activity_heat_map(selected_user, df)
        fig, ax = plt.subplots()
        ax = sns.heatmap(user_heatmap)
        st.pyplot(fig)

        # ---------------- Most Busy Users ----------------
        if selected_user == 'Overall':
            st.title("Most Busy Users")
            try:
                x, new_df = helper.most_busy_users(df)
                fig, ax = plt.subplots()
                ax.bar(x.index, x.values, color="red")
                plt.xticks(rotation='vertical')
                col1, col2 = st.columns(2)
                with col1:
                    st.pyplot(fig)
                with col2:
                    st.dataframe(new_df)
            except Exception as e:
                st.error(f"Error in most_busy_users: {e}")

        # ---------------- Wordcloud ----------------
        st.title("WordCloud")
        try:
            df_wc = helper.create_wordcloud(selected_user, df)
            if df_wc is None:
                st.write("WordCloud could not be generated (no data).")
            else:
                fig, ax = plt.subplots()
                ax.imshow(df_wc, interpolation='bilinear')
                ax.axis("off")
                st.pyplot(fig)
        except Exception as e:
            st.write("WordCloud could not be generated:", e)

        # ---------------- Most Common Words ----------------
        st.title("Most Common Words")
        try:
            most_common_df = helper.most_common_words(selected_user, df)
            if most_common_df is None or most_common_df.empty:
                st.write("No word frequency data available.")
            else:
                mc = most_common_df.copy()
                mc = mc.iloc[:, :2]
                mc.columns = ['word', 'count']
                fig, ax = plt.subplots()
                ax.barh(mc['word'], mc['count'])
                plt.xlabel("Count")
                st.pyplot(fig)
        except Exception as e:
            st.error(f"Error in most_common_words: {e}")

        # ---------------- Emoji analysis --------------------------
        st.title("Emoji Analysis")
        try:
            emoji_df = helper.emoji_helper(selected_user, df)
            if emoji_df is None or emoji_df.empty:
                st.write("No emojis found.")
            else:
                if 0 in emoji_df.columns and 1 in emoji_df.columns:
                    emoji_df = emoji_df.rename(columns={0: "emoji", 1: "count"})

                emoji_df = emoji_df.iloc[:, :2]
                emoji_df.columns = ['emoji', 'count']

                col1, col2 = st.columns(2)
                with col1:
                    st.dataframe(emoji_df)

                with col2:
                    top = emoji_df.head(10).copy()
                    if len(emoji_df) > 10:
                        others = emoji_df["count"].iloc[10:].sum()
                        top = pd.concat(
                            [top, pd.DataFrame([{"emoji": "Others", "count": others}])],
                            ignore_index=True
                        )

                    fig, ax = plt.subplots()

                    # ✅ Fix emoji font
                    from matplotlib import rcParams
                    rcParams['font.family'] = emoji_font

                    wedges, texts, autotexts = ax.pie(
                        top["count"],
                        labels=top["emoji"],
                        autopct="%1.1f%%",
                        startangle=90,
                        textprops={"fontsize": 12}
                    )

                    # ✅ Force correct font for labels
                    for text in texts + autotexts:
                        text.set_fontfamily(emoji_font)

                    ax.axis("equal")
                    st.pyplot(fig)
        except Exception as e:
            st.error(f"Error in emoji analysis: {e}")
