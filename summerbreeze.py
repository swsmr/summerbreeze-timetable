from datetime import time

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

dates = {
    0: "13.08.2025",
    1: "13.08.2025",
    2: "13.08.2025",
    3: "13.08.2025",
    4: "14.08.2025",
    5: "14.08.2025",
    6: "14.08.2025",
    7: "14.08.2025",
    8: "15.08.2025",
    9: "15.08.2025",
    10: "15.08.2025",
    11: "15.08.2025",
    12: "16.08.2025",
    13: "16.08.2025",
    14: "16.08.2025",
    15: "16.08.2025",
    16: "12.08.2025",
}


@st.cache_data(ttl=300)
def fetch_data(extract_links="body"):
    dfs = pd.read_html(
        "https://www.summer-breeze.de/en/running-order/", extract_links=extract_links
    )
    for i, df in enumerate(dfs):
        if extract_links == "body":
            df.iloc[:, 0] = df.iloc[:, 0].str[0]
            df.iloc[:, 1] = df.iloc[:, 1].str[0]
            df.iloc[:, 2] = df.iloc[:, 2].str[1]
        df["Stage"] = df.columns[0]
        df["Day"] = dates[i]
        df.columns = ["Time", "Band", "Link", "__dummy2__", "Stage", "Day"]
        df["Start"] = df["Time"].str.split("  ", expand=True)[0]
        df["End"] = df["Time"].str.split("  ", expand=True)[1]
        df["Time"] = df["Time"].str.replace("  ", " - ")
        df["Starttime"] = pd.to_datetime(
            dates[i] + " " + df["Start"], format="%d.%m.%Y %H:%M"
        )
        df["Endtime"] = pd.to_datetime(
            dates[i] + " " + df["End"], format="%d.%m.%Y %H:%M"
        )
        df.loc[df["Starttime"].dt.time < time(6, 0), "Starttime"] = df[
            "Starttime"
        ] + pd.Timedelta(days=1)
        df.loc[df["Endtime"].dt.time < time(6, 0), "Endtime"] = df[
            "Endtime"
        ] + pd.Timedelta(days=1)
        df["Midtime"] = df["Starttime"] + (df["Endtime"] - df["Starttime"]) / 2
        df["Duration"] = df["Endtime"] - df["Starttime"]
    df = pd.concat(dfs, ignore_index=True)
    return df


def show_links_to_band_info(df):
    df = df.sort_values(["Stage", "Starttime"])
    cols = st.columns(len(df["Stage"].unique()))
    for i, stage in enumerate(df["Stage"].unique()):
        cols[i].write(f"**{stage}**")
    for i, stage in enumerate(df["Stage"].unique()):
        with cols[i]:
            stage_df = df[df["Stage"] == stage]
            for _, row in stage_df.iterrows():
                st.markdown(f"{row['Time']} [{row['Band']}]({row['Link']})")


def create_timetable(df, title=None):
    fig_bar = (
        alt.Chart(df, height=800, title=title)
        .mark_bar()
        .encode(
            y=alt.Y("Starttime", scale=alt.Scale(reverse=True)),
            y2="Endtime",
            x=alt.X("Stage", axis=alt.Axis(orient="top", title=None, labelAngle=30)),
            color=alt.Color("Stage", legend=None),
            href="Link",
        )
    )
    fig_band_text = (
        alt.Chart(df)
        .mark_text(dy=-5)
        .encode(
            y="Endtime",
            x="Stage",
            text="Band",
        )
    )
    fig_time_text = (
        alt.Chart(df)
        .mark_text(dy=7)
        .encode(
            y="Starttime",
            x="Stage",
            text="Time",
        )
    )
    fig = fig_bar + fig_band_text + fig_time_text
    now = pd.Timestamp.now() + pd.Timedelta(2, "hours")
    if now >= df["Starttime"].min() and now <= df["Endtime"].max():
        fig_now = (
            alt.Chart(pd.DataFrame({"y": [now]}))
            .mark_rule(color="gray", strokeDash=[4, 4])
            .encode(y="y")
        )
        fig += fig_now
    return fig


def all_timetables_page():
    df = st.session_state.df
    df = df.sort_values("Day")
    for i, day in enumerate(df["Day"].unique()):
        day_df = df[df["Day"] == day]
        fig = create_timetable(day_df, title=day_formatter(day))
        st.altair_chart(fig, theme=None)


def day_formatter(day):
    return f"{pd.to_datetime(day, format='%d.%m.%Y').day_name()[:3]} {pd.to_datetime(day, format='%d.%m.%Y').strftime('%d.')}"


def interactive_timetable():
    st.title("Summer Breeze 2025")
    df = st.session_state.df

    # Filter the data
    only_upcoming = st.toggle("Show only upcoming bands")
    if only_upcoming:
        df = df[df["Endtime"]] > (pd.Timestamp.now() + pd.Timedelta(2, "hours"))
    selected_day = st.pills(
        "Select day",
        np.sort(df["Day"].unique()),
        default=np.sort(df["Day"].unique())[0],
        format_func=day_formatter,
    )
    df = df[df["Day"] == selected_day]

    tabs = st.tabs(["Timetable", "Bands"])

    with tabs[0]:
        fig = create_timetable(df, title="")  # day_formatter(selected_day)
        st.altair_chart(fig, theme=None)

    with tabs[1]:
        show_links_to_band_info(df)


def when_plays_who():
    df = st.session_state.df
    bands = np.sort(df["Band"].unique())
    selected_band = st.selectbox("Select band", bands)
    band_df = df[df["Band"] == selected_band]
    st.markdown(f"{day_formatter(band_df['Day'].iloc[0])}, {band_df['Time'].iloc[0]} | {band_df['Stage'].iloc[0]} | [Link]({band_df['Link'].iloc[0]})")


def main():
    # Streamlit set up
    st.set_page_config(
        page_title="Summer Breeze 2025",
        page_icon=":guitar:",
        layout="centered",
        initial_sidebar_state="collapsed",
    )

    # Fetch and clean the data
    st.session_state.df = fetch_data()

    # Page navigation
    pg = st.navigation(
        [
            st.Page(interactive_timetable, title="Home", icon=":material/dashboard:"),
            st.Page(all_timetables_page, title="All timetables", icon=":material/calendar_clock:"),
            st.Page(when_plays_who, title="Bands", icon=":material/artist:"),
        ],
        position="top", 
    )
    pg.run()


if __name__ == "__main__":
    main()
