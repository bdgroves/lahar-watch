# The sensor network around Mount Rainier

The dashboard builds its station list from the [EarthScope](https://www.earthscope.org/) (IRIS) FDSN station
service every hour, so `data/stations.json` on the `data` branch is the authoritative list: every current
seismometer and infrasound sensor in the **CC** (USGS Cascades Volcano Observatory) and **UW** (Pacific
Northwest Seismic Network) networks within about 55 km of the summit, with location, elevation, sensors,
installation date, whether it reported in the last 20 minutes, and its ground-motion level.

## The lahar detection system

- Operating since **1998** (acoustic flow monitors and tripwires in the Carbon and Puyallup valleys).
- Modernised from **2017**: real-time broadband seismometers, infrasound arrays, webcams and GPS; 14 new sites
  by spring 2021, with the network expected to exceed 40 real-time stations when complete
  ([USGS](https://www.usgs.gov/volcanoes/mount-rainier/science/monitoring-lahars-mount-rainier)).
- **April 2022:** Mount Rainier National Park approved nine new stations on the southwest side, in the Puyallup
  and Nisqually watersheds, two of them (Mount Wow and Tahoma Bridge) directly in lahar paths
  ([Auburn Reporter](https://www.auburn-reporter.com/northwest/mount-rainier-park-approves-nine-new-lahar-monitoring-stations/)).
  In the station catalogue, CC.WOW and CC.TABR start in September 2022.
- **Autumn 2025:** White River stations CC.GRWR (Greenwater), CC.PALI (Palisades) and CC.SUNT (Sun Top) start on
  8 September 2025, and CC.LONR (Lonesome Lake) on 2 October 2025.
- Data from each site reach the 24-hour emergency operations centres at Washington Emergency Management and
  South Sound 911 within 10 seconds; alerts go out through All Hazard Alert Broadcast sirens from Orting to the
  Port of Tacoma, the Emergency Alert System and NOAA Weather Radio (USGS).

## Warning time (published figures)

| | Time | Source |
|---|---|---|
| Residential areas inside the park | about 5 minutes | USGS |
| Residential areas outside the park | 15–60 minutes | USGS |
| Most communities, once a large lahar is detected | at least 40 minutes, up to 3 hours | USGS, 2020 |
| Worst-case west-flank landslide lahar (260 million m³), Tahoma Glacier headwall | Ashford ~20 min; head of Alder Lake ~50 min | George and others, 2022 (OFR 2021-1118) |
| The same, from the Sunset Amphitheater | Orting lowlands ~1 hour, front ~4 m deep at ~4 m/s | George and others, 2022 |
