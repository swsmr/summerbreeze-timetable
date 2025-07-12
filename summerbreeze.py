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


def main():
    st.set_page_config(
        page_title="Summer Breeze 2025",
        page_icon=":guitar:",
    )
    st.title("Summer Breeze 2025")
    df = fetch_data()
    
    only_upcoming = st.toggle("Only show upcoming bands")
    if only_upcoming:
        df = df[df["Endtime"] > pd.Timestamp.now()]
    selected_day = st.pills(
        "Select day",
        np.sort(df["Day"].unique()),
        default=np.sort(df["Day"].unique())[0],
    )
    df = df[df["Day"] == selected_day]

    # Timetable
    st.header("Timetable")

    # Plotly express
    # import plotly.express as px
    # fig = px.timeline(
    #     df,
    #     x_start="Starttime",
    #     x_end="Endtime",
    #     text="Band",
    #     y="Stage",
    #     color="Stage",
    # )
    # fig.update_layout(showlegend=False)
    # fig.update_layout(margin={"t": 20, "r": 20})
    # fig.update_layout(yaxis_title=None)
    # fig.update_yaxes(tickangle=-75)
    # fig.update_xaxes(showgrid=True)
    # fig.update_traces(textangle=-90, textposition="inside")
    # # fig.show()
    # # fig.show("browser")
    # st.plotly_chart(fig)

    # Altair
    fig_bar = (
        alt.Chart(df, height=800)
        .mark_bar()
        .encode(
            y=alt.Y("Starttime", scale=alt.Scale(reverse=True)),
            y2="Endtime",
            x=alt.X("Stage", axis=alt.Axis(orient="top")),
            color=alt.Color("Stage", legend=None),
            href="Link",
        )
    )
    # fig_bar["usermeta"] = {"embedOptions": {"loader": {"target": "_blank"}}} # Not working...
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
    st.altair_chart(fig, theme=None)

    # Altair with selection (not working on mobile)
    # point_selector = alt.selection_point("point_selection")
    # fig_bar = (
    #     alt.Chart(df, height=800)
    #     .mark_bar()
    #     .encode(
    #         y=alt.Y("Starttime", scale=alt.Scale(reverse=True)),
    #         y2="Endtime",
    #         x=alt.X("Stage", axis=alt.Axis(orient="top", labelAlign="left")),
    #         color=alt.Color("Stage", legend=None),
    #     )
    # ).add_params(point_selector)
    # event = st.altair_chart(fig_bar, theme=None, on_select="rerun")
    # st.write(event)

    # Displaying links as they don't work in Altair on mobile somehow
    # df["Link"] += "#" + df["Band"]
    # st.write(df)
    # st.dataframe(
    #     df[["Stage", "Time", "Band", "Link"]].pivot_table(
    #         index="Time",
    #         columns="Stage",
    #         values="Link",
    #         aggfunc="max",
    #     ),
    #     column_config={
    #         stage: st.column_config.LinkColumn(stage, display_text="https://.+?#(.+)")
    #         for stage in df["Stage"].unique()
    #     },
    # )

    st.header("Links")
    df = df.sort_values("Starttime")
    cols = st.columns(len(df["Stage"].unique()))
    for i, stage in enumerate(df["Stage"].unique()):
        cols[i].write(f"**{stage}**")
    for i, stage in enumerate(df["Stage"].unique()):
        with cols[i]:
            stage_df = df[df["Stage"] == stage]
            for _, row in stage_df.iterrows():
                st.markdown(
                    f"{row['Time']} [{row['Band']}]({row['Link']})"
                )


if __name__ == "__main__":
    main()
