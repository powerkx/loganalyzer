set -e

start_time="2016-11-25 00:00"
end_time="2016-11-26 00:00"
log_folder="2016-11-25"

# fetch data
python fetch_users.py
python fetch_redirects.py
python fetch_logs.py "$log_folder"

# import configs
python loganalyzer.py import --defaults  

# import logs
python loganalyzer.py import --logs "logs/$log_folder"

# update collections
python loganalyzer.py update --all "$start_time" "$end_time"

time_c=$(date +%Y-%m-%d-%H)00
mkdir -p "result_csv/$time_c"

# output result csv
python loganalyzer.py report --users -n "$start_time" "$end_time" > "result_csv/$time_c/users.csv"
python loganalyzer.py report --user-event -n "$start_time" "$end_time" > "result_csv/$time_c/user_event.csv"
python loganalyzer.py report --quality -n "$start_time" "$end_time" > "result_csv/$time_c/quality.csv"
python loganalyzer.py report --fps -n "$start_time" "$end_time" > "result_csv/$time_c/fps.csv"
python loganalyzer.py report --memory -n "$start_time" "$end_time" > "result_csv/$time_c/memory.csv"
python loganalyzer.py report --sessions -n "$start_time" "$end_time" > "result_csv/$time_c/sessions.csv"

python loganalyzer.py report --context3d-info -n "$start_time" "$end_time" > "result_csv/$time_c/context3d_info.csv"
python loganalyzer.py report --os-info -n "$start_time" "$end_time" > "result_csv/$time_c/os_info.csv"
python loganalyzer.py report --browser-info -n "$start_time" "$end_time" > "result_csv/$time_c/browser_info.csv"
python loganalyzer.py report --fp-version-info -n "$start_time" "$end_time" > "result_csv/$time_c/fp_version_info.csv"

python loganalyzer.py report --intervals -n "$start_time" "$end_time" > "result_csv/$time_c/intervals.csv"
python loganalyzer.py report --retention -n "$start_time" "$end_time" > "result_csv/$time_c/retention.csv"
