# WhatAPI

What, Python style.

## API Endpoints

### GET /what/torrents/search

GET parameters must be properly URL-encoded, with the exception that spaces may be replaced by a "+" sign. Parameters may be any combination of the following options:

* page: page of results to show. each page shows 50 results (e.g. page=1 shows 1-50, page=2 shows 51-100, etc.)
* artistname: artist name
* groupname: album/torrent name
* recordlabel: record label
* cataloguenumber: catalogue number
* year: year of original release
* remastertitle: remaster title
* remasteryear: remaster release year
* remasterrecordlabel: remaster record label
* remastercataloguenumber: remaster catalogue number
* filelist: file name list
* taglist: comma-separated list of tags to match. use !tag to exclude tag.

* bitrate:
> * 192
> * APS (VBR)
> * V2 (VBR)
> * V1 (VBR)
> * 256
> * APX (VBR)
> * V0 (VBR)
> * q8.x (VBR)
> * 320
> * Lossless
> * 24bit Lossless

* format:
> * MP3
> * FLAC
> * Ogg Vorbis
> * AAC
> * AC3
> * DTS

* media:
> * CD
> * DVD
> * Vinyl
> * Soundboard
> * SACD
> * DAT
> * Cassette
> * WEB
> * Blu-ray

* releasetype:
> * 1
> * 3
> * 5
> * 6
> * 7
> * 9
> * 11
> * 13
> * 14
> * 15
> * 16
> * 21

* haslog:
> * 1
> * 0
> * 100
> * -1

* hascue:
> * 1
> * 0

* scene:
> * 0 - show only groups that do not have any scene torrents
> * 1 - show only groups that have at least one scene torrent

* freetorrent:
> * 0 - show only groups that do not have any freeleech torrents
> * 1 - show only groups that have at least one freeleech torrent

* tags_type: 
> * 0 - match any tag in taglist
> * 1 - match all tags in taglist

* order_by: 
> * time - orders by uploaded time of most recent torrent in group
> * size - orders by size of largest torrent in group
> * snatched - orders by total snatches for all torrents in group
> * seeders - orders by total seeders for all torrents in group
> * leechers - orders by total leechers for all torrents in group

* order_way:
> * asc - sort ascending
> * desc - sort descending
  
JSON return:

<pre>
options: {
  all: "client-",
  provided: "GET",
  params: "passed",
  to: "the",
  search: "page."
},
results: {
  time: 140.5 /* time spent processing request in milliseconds */
  result_count: 1000 /* total results on what.cd */
  results_more: 1 /* indicates if result_count shows with a + sign on the site. site shows 1000+ for pages 1-10, 1500+ for pages 11-20, 2000+ for pages 21-30, etc... n+, where n = 1000 + 500*floor((page-1)/10) */
  result_first: 1 /* index of first result on page (page_number * 50 - 49) */
  result_last: 50 /* index of last result on page (result_first + group_count) */
  group_count: 50 /* groups returned */
  groups: [ 
    /* groups are ordered the same as the results from what.cd */
    {
      result: 1,
      id: 12,
      type: "music"
      name: "group name"
      artist_id: 23,
      artist_name: "group name",
      year: 2011,
      tags: ["tag", "another.tag"],
      torrent_ids: [234,345,456]
    }, { ... }, { ... }
  ],
  torrent_count: 312 /* torrents shown on this page */
  torrents: [
    {
      id: 234,
      edition_str: "2011 - Title / Label / Cat#",
      edition: {
        year: 2011,
        title: "Title",
        label: "Record label",
        cat_number: "Cat#"
      }
      group_id: 12,
      format: "FLAC",
      bitrate: "Lossless",
      log: 1,
      log_score: 100,
      cue: 1,
      media: "CD",
      files: 17,
      uploaded: 827493024, /* unix timestamp */
      size: "123.21 MB",
      seeders: 1,
      leechers: 2,
      snatches: 3
    }, { ... }, { ... }
  ]
}
</pre>