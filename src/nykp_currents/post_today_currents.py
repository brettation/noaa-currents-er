from argparse import ArgumentParser
from dataclasses import dataclass
import numpy as np
import pandas as pd
import pdb
from traceback import print_exception
from typing import Optional

from utils.data import rename_cols
from utils.noaa import retrieve_currents_table
from utils.slack import post_message


@dataclass
class Station:
    name: str
    id: str


DEFAULT_NYKP_STATION = Station('Hudson River Entrance', 'NYH1927_13')


def knots_to_mph(knots) -> Optional[float]:
    try:
        if isinstance(knots, str):
            knots = float(knots)
        return knots * 1.15078
    except (TypeError, ValueError):
        return np.nan


def format_currents_table(df: pd.DataFrame) -> str:
    col_renames = {'Date_Time (LST/LDT)': 'time',
                   'Event': 'stage',
                   'Speed (knots)': 'knots'}
    df = rename_cols(df, col_renames)
    df['mph'] = df['knots'].apply(knots_to_mph)
    text = ''
    for _, row in df.iterrows():
        text += f"{row['time']}  "
        text += row['stage']
        if pd.notna(row['mph']):
            text += f" ({row['mph']:.1f} mph)"
        text += '\n'
    return text


def post_currents(station: Optional[Station] = None, date=None, time_period=None):
    if station is None:
        station = DEFAULT_NYKP_STATION
    predictions = retrieve_currents_table(station_id=station.id, date=date, time_period=time_period)
    table_txt = format_currents_table(predictions.table)
    post_txt = f"*New NOAA current predictions at {station.name}*\n{predictions.link}\n\n{table_txt}"
    response = post_message(post_txt)
    return response


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--date', type=str, default=None)
    parser.add_argument('--station', type=str, default=None)
    parser.add_argument('--range', type=str, default=None)
    parser.add_argument('--pdb', action='store_true')
    args = parser.parse_args()

    if args.pdb:
        pdb.set_trace()

    if args.station is not None:
        station = Station(id=args.station, name=f"Station {args.station}")
    else:
        station = None
    try:
        post_currents(station=station, date=args.date, time_period=args.range)
    except:
        print_exception()
        pdb.post_mortem()