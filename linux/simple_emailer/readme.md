simple emailer that can include images drive by a mqtt topic and optional payload
Done in the style of the micropython apps with an install.py reading a toml configuration ythat generates a cfg.py.
it does no IO when running just waiting on a mqtt subscribe(s) and sending a pre defined email with jpg images.
