set -e

start_time="2016-12-01 00:00"
end_time="2016-12-02 00:00"
log_folder="2016-12-01"

# fetch data
python3 fetch_users.py
python3 fetch_redirects.py
python3 fetch_logs.py "$log_folder"

# import configs
python3 loganalyzer.py import --defaults  

# import logs
python3 loganalyzer.py import --logs "logs/$log_folder"

# update collections
python3 loganalyzer.py update --all "$start_time" "$end_time"

time_c=$(date +%Y-%m-%d-%H)00
mkdir -p "result_csv/$time_c"

# output result csv
python3 loganalyzer.py report --users -n "$start_time" "$end_time" > "result_csv/$time_c/users.csv"
python3 loganalyzer.py report --user-event -n "$start_time" "$end_time" > "result_csv/$time_c/user_event.csv"
python3 loganalyzer.py report --quality -n "$start_time" "$end_time" > "result_csv/$time_c/quality.csv"
python3 loganalyzer.py report --fps -n "$start_time" "$end_time" > "result_csv/$time_c/fps.csv"
python3 loganalyzer.py report --memory -n "$start_time" "$end_time" > "result_csv/$time_c/memory.csv"
python3 loganalyzer.py report --sessions -n "$start_time" "$end_time" > "result_csv/$time_c/sessions.csv"

python3 loganalyzer.py report --context3d-info -n "$start_time" "$end_time" > "result_csv/$time_c/context3d_info.csv"
python3 loganalyzer.py report --os-info -n "$start_time" "$end_time" > "result_csv/$time_c/os_info.csv"
python3 loganalyzer.py report --browser-info -n "$start_time" "$end_time" > "result_csv/$time_c/browser_info.csv"
python3 loganalyzer.py report --fp-version-info -n "$start_time" "$end_time" > "result_csv/$time_c/fp_version_info.csv"

python3 loganalyzer.py report --intervals -n "$start_time" "$end_time" > "result_csv/$time_c/intervals.csv"
python3 loganalyzer.py report --retention -n "$start_time" "$end_time" > "result_csv/$time_c/retention.csv"
