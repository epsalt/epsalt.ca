---
type: project
template: project
title: 'Wavething: Audio Waveforms'
date: 2022-02-26 21:30:00 -0700
updated: 2022-02-26 21:30:00 -0700
slug: wavething
thumb: wavething/twitter.png
source: https://github.com/epsalt/wavething
summary: A small D3.js and React app for generating audio waveforms.
---

<div uk-alert class="uk-alert-primary">
The app is live <a href="https://wavething.epsalt.ca">here</a>! Try it out
with your own audio file.
</div>

Wavething is a simple app for creating and styling audio
waveforms. Audio waveform charts display the volume of an audio file
over time. When the wave is taller, the audio is louder.

![Wavething Screenshot](/images/wavething/wavething.png)

This project was an experiment to see how well React and D3 work
together. [Amelia Wattenberger's post](https://wattenberger.com/blog/react-and-d3) 
about this topic was a great resource. I took the lazy approach and
cleared the SVG element in the `useEffect` hook on each data update. A
better way to do this would be to let D3 control data
entry/exit/updates instead of recreating the chart from scratch on
each update.

## Tech
- React
- D3.js
- waveform-data.js


