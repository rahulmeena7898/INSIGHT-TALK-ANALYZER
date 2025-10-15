# # import re
# # import pandas as
# def preprocess(data):
#     # 1. WhatsApp datetime पहचानने का regex
#     pattern = r"\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}(?:\s?[APMapm]{2})?\s-\s"
#
#     # 2. Chat data से messages और dates निकालना
#     messages = re.split(pattern, data)[1:]
#     dates = re.findall(pattern, data)
#
#     # 3. Dates से " -" हटाना
#     clean_dates = [d.strip(" -") for d in dates]
#
#     # 4. DataFrame बनाना
#     df = pd.DataFrame({'date': clean_dates, 'user_message': messages})
#
#     # 5. Date को proper datetime में बदलना
#     df['date'] = pd.to_datetime(df['date'], errors="coerce", infer_datetime_format=True)
#
#     # 6. User और message अलग करना
#     df[['user', 'message']] = df['user_message'].str.extract(r'([\w\W]+?):\s(.*)')
#
#     # 7. System/group messages संभालना
#     df['user'] = df['user'].fillna('group_notification')
#     df['message'] = df['message'].fillna(df['user_message'])
#
#     # 8. Extra column हटाना
#     df = df.drop(columns=['user_message'])
#
#     # 9. Extra features निकालना
#     df['year'] = df['date'].dt.year
#     df['month'] = df['date'].dt.month_name()
#     df['day'] = df['date'].dt.day
#     df['hour'] = df['date'].dt.hour
#     df['minute'] = df['date'].dt.minute
#
#     return df


import re
import pandas as pd

def preprocess(data):
    # Normalize spaces (fix iPhone special whitespace issues)
    data = data.replace('\u202f', ' ').replace('\u200e', '')

    # WhatsApp datetime regex (Android + iOS support)
    pattern = (
        r"\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}(?:\s?[APMapm]{2})?\s-\s"   # Android/iOS normal
        r"|\[\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}:\d{2}\]"                # iPhone export
    )

    # Split messages & dates
    messages = re.split(pattern, data)
    dates = re.findall(pattern, data)

    if not messages or not dates:
        return pd.DataFrame(columns=[
            'date','user','message','year','month','month_num','day',
            'day_name','hour','minute','only_date','period'
        ])

    messages = messages[1:]
    clean_dates = [d.strip(" -") for d in dates]

    if len(messages) != len(clean_dates):
        min_len = min(len(messages), len(clean_dates))
        messages = messages[:min_len]
        clean_dates = clean_dates[:min_len]

    df = pd.DataFrame({'date': clean_dates, 'user_message': messages})

    # Convert date
    df['date'] = pd.to_datetime(df['date'], errors="coerce", infer_datetime_format=True)

    # Split user & message
    users_messages = df['user_message'].str.extract(r'^(.*?):\s(.*)')
    df['user'] = users_messages[0]
    df['message'] = users_messages[1]

    # Handle group/system messages
    df['user'] = df['user'].fillna('group_notification')
    df['message'] = df['message'].fillna(df['user_message'])

    df = df.drop(columns=['user_message'])

    # Extra datetime features
    df['only_date'] = df['date'].dt.date
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute

    # For heat map (period column)
    period = []
    for hour in df['hour']:
        if hour == 23:
            period.append(f"{hour}-00")
        elif hour == 0:
            period.append(f"00-{hour+1}")
        else:
            period.append(f"{hour}-{hour+1}")

    df['period'] = period

    return df
