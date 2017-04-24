---
type: post
title: Roadtrip
date: 2017-xx-xx xx:xx:xx -0700
url: roadtrip
tags: r
      cartography
      ggplot2
      travel
---

In August of 2016 I took advantage of unemployment to roadtrip
across the United States. My friend was moving from New York
City to Vancouver and had some precious cargo that he didn't
want to ship by air. It was a great trip. Along the we spent a
lot of time in national parks and I got badly sunburned on a
couple occasions.

![Joshua Tree](/images/joshua_tree.jpeg)

*Sunset in Joshua Tree*

The entire time we were travelling I had Google location history
turned on and thought it would be a fun project to map out our path
across the United States. 

## Source Data

First I downloaded my location data from Google using
the [Google Takeout][google-takeout] tool. There are two options for
downloading your data, [JSON][json] and [KML][kml]. I went with JSON
for this project, but the KML file can be easily loaded in to Google
Earth or other GIS software. I've had location tracking enabled since
2011, my data file is ~20 MB gzip'd and a ~300 MB uncompressed JSON
file.

Here's a sample of how the JSON is structured:

```json
{
    "locations": [{
        "timestampMs": "1472048632150",
        "latitudeE7": 510354955,
        "longitudeE7": -1140796058,
        "accuracy": 22,
        "activitys": [{
            "timestampMs": "1472048632075",
            "activities": [{
                "type": "still",
                "confidence": 100
            }]
        }]
    }, {
        "timestampMs": "1472048258184",
        "latitudeE7": 510354955,
        "longitudeE7": -1140796058,
        "accuracy": 22
    }]
}
```

The JSON file has the following key/value pairs:

| Name        | Units                                |
|-------------|--------------------------------------|
| timestampMS | milliseconds (POSIX time)            | 
| longitudeE7 | decimal degrees \* 10<sup>7</sup>    |
| longitudeE7 | decimal degrees \* 10<sup>7</sup>    |
| accuracy    | meters                               |
| activities  | {type (activity), confidence (%)}    |

Although all we need to make a map is longitude and latitude. I also
am going to want to filter down to only the dates that I have been on
my trip, so the timestamp column is required.

Google estimates what type of motion you are in (e.g. still, walking,
running, onBicycle) during sections of each recording. This
information is cool (and kind of scary), but I didn't use it in this
analysis.

## Cleanup

Now that we've secured our location history file, things start to get
a little more fun. The end goal is to use [ggplot2][ggplot2] to map
our path, so we need to convert from JSON to an R data frame. I'm
going to walk through the R code I used to transform the JSON into a
data frame in the format ggplot2 requires. If you aren't interested in
this part of the process, skip to [down to the mapping section.](#first-look)

First we have to load our JSON file. We are going to use
the [RJSONIO][rjsonio] package to read our JSON.

~~~r
library(RJSONIO)
loc_file <- "data/loc_history.json"
loc <- fromJSON(loc_file)

> str(loc)
> List of 1
>  $ locations:List of 1029285
> ..$ :List of 5
> .. ..$ timestampMs: chr "1472048798254"
> .. ..$ latitudeE7 : num 5.1e+08
> .. ..$ longitudeE7: num -1.14e+09
> .. ..$ accuracy   : num 22
> .. ..$ activitys  :List of 2
> .. .. ..$ :List of 2
> .. .. .. ..$ timestampMs: chr "1472048797114"
> .. .. .. ..$ activities :List of 6
~~~

RJSONIO doesn't output a data frame, it actually produces a list of
lists that more closely matches how the actual JSON is structured. We
can convert our list of lists to a data frame using a couple of the R
languages more magical array manipulation functions `lapply` and `do.call`.

~~~r
## Drop everything except timestamp, lat, long
dropped <- lapply(loc[[1]], function(a) a[1:3])

## Convert list of strings to data.frame
loc_df <- do.call(rbind.data.frame, dropped)

> str(loc_df)
> 'data.frame':	1029285 obs. of  3 variables:
>  $ timestampMs: chr  "1472048798254" "1472048632150" "1472048258184" "1472047883561" ...
>  $ latitudeE7 : num  5.1e+08 5.1e+08 5.1e+08 5.1e+08 5.1e+08 ...
>  $ longitudeE7: num  -1.14e+09 -1.14e+09 -1.14e+09 -1.14e+09
~~~

This output is quite close to where we want to be. Our final problem
is that our time and coordinates are not in the units we want for our
final map. The code below converts our date and coordinates columns
into more standard units.

~~~r
library(magrittr) # embrace the pipe!

loc_df$date <-
    loc_df$timestampMs %>%
    as.numeric %>%
    {./1000} %>% ## miliseconds to seconds
    as.POSIXct(origin="1970-01-01") %>%
    as.Date
    
loc_df$long <- loc_df$longitudeE7 / 10^7
loc_df$lat  <- loc_df$latitudeE7 / 10^7

> str(loc_df)
> 'data.frame':	1029285 obs. of  6 variables:
>  $ timestampMs: chr  "1472048798254" "1472048632150" "1472048258184" "1472047883561" ...
>  $ latitudeE7 : num  5.1e+08 5.1e+08 5.1e+08 5.1e+08 5.1e+08 ...
>  $ longitudeE7: num  -1.14e+09 -1.14e+09 -1.14e+09 -1.14e+09 -1.14e+09 ...
>  $ date       : Date, format: "2016-08-24" "2016-08-24" ...
>  $ long       : num  -114 -114 -114 -114 -114 ...
>  $ lat        : num  51 51 51 51 51 ...
~~~

If you aren't familiar with the `%>%` operator in R, it is
a [the forward pipe operator][pipe] implemented in
the [magrittr][magrittr] package. Pipes are used to chain functions
together, a concept very commonly utilized in [unix][unix-pipelines].

~~~r
## Filter only days in trip
trip <- ldf[ldf$date > as.Date("2016-07-28") & ldf$date < as.Date("2016-08-11"),]

## Remove outliers
trip <- trip[trip$long < -50,]
~~~

R doesn't have a reputation as a particularly speedy language and I
haven't done any optimization. The above code took about 12 minutes to
process a ~300 MB JSON file on my 2013 MacBook Air. There is room for
improvement here, likely in the JSON load and the `do.call` line. I
only needed to run this code once so the speed wasn't a priority.

**Side note:** when I was just starting out writing R
code I was fortunate to read [The R Inferno][inferno] by Patrick
Burns. It is a well written reference on the subtleties of the R
language told in the form of Dante's Inferno. Give it a look if you
want to learn more about R why has such a *complicated*
reputation.

## First Look

Now that we have our coordinates in a more workable format we
can start having a look. This is what my trip looks like using
the stock R plotting function.

~~~r
> plot(trip$lat, trip$long)
~~~

![USA Map](/images/usa_map_no_proj.png)

We can immediately see some data quality issues. My Google
location history doesn't cover the whole trip equally. There are
times when we have no data at all. This could either be due to
my phone running out of batteries which happened a few times
during the trip, rural areas with poor GPS coverage, or adverse
weather conditions. Although we have some quality issues this
data is more than acceptable. We are making a rather coarse map
and the gaps aren't anything that a little interpolation can't
fix.

## Plotting with ggplot2

There are a few more things we need to do in order to transform
our data into something that can actually be called a map.

+ Use an appropriate map projection
+ Add geographical borders (in this case US state boundaries)
+ Note the places that we stopped on our trip

Luckily ggplot2 can help us out with all of these:

[gmaps-timeline]: https://www.google.ca/maps/timeline
[google-takeout]: https://takeout.google.com/
[json]: http://www.json.org
[rjsonio]: https://cran.r-project.org/web/packages/RJSONIO/index.html
[kml]: https://developers.google.com/kml/
[ggplot2]: http://docs.ggplot2.org/current/
[r]: https://www.r-project.org/
[inferno]: http://www.burns-stat.com/pages/Tutor/R_inferno.pdf"
[pipe]: http://blog.revolutionanalytics.com/2014/07/magrittr-simplifying-r-code-with-pipes.html
[magrittr]: https://cran.r-project.org/web/packages/magrittr/
[unix-pipelines]: https://en.wikipedia.org/wiki/Pipeline_(Unix)