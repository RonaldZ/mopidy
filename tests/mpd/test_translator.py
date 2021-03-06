from __future__ import absolute_import, unicode_literals

import unittest

from mopidy.internal import path
from mopidy.models import Album, Artist, Playlist, TlTrack, Track
from mopidy.mpd import translator


class TrackMpdFormatTest(unittest.TestCase):
    track = Track(
        uri='a uri',
        artists=[Artist(name='an artist')],
        name='a name',
        album=Album(
            name='an album', num_tracks=13,
            artists=[Artist(name='an other artist')]),
        track_no=7,
        composers=[Artist(name='a composer')],
        performers=[Artist(name='a performer')],
        genre='a genre',
        date='1977-01-01',
        disc_no=1,
        comment='a comment',
        length=137000,
    )

    def setUp(self):  # noqa: N802
        self.media_dir = '/dir/subdir'
        path.mtime.set_fake_time(1234567)

    def tearDown(self):  # noqa: N802
        path.mtime.undo_fake()

    def test_track_to_mpd_format_for_empty_track(self):
        # TODO: this is likely wrong, see:
        # https://github.com/mopidy/mopidy/issues/923#issuecomment-79584110
        result = translator.track_to_mpd_format(Track())
        self.assertIn(('file', ''), result)
        self.assertIn(('Time', 0), result)
        self.assertIn(('Artist', ''), result)
        self.assertIn(('Title', ''), result)
        self.assertIn(('Album', ''), result)
        self.assertIn(('Track', 0), result)
        self.assertNotIn(('Date', ''), result)
        self.assertEqual(len(result), 6)

    def test_track_to_mpd_format_with_position(self):
        result = translator.track_to_mpd_format(Track(), position=1)
        self.assertNotIn(('Pos', 1), result)

    def test_track_to_mpd_format_with_tlid(self):
        result = translator.track_to_mpd_format(TlTrack(1, Track()))
        self.assertNotIn(('Id', 1), result)

    def test_track_to_mpd_format_with_position_and_tlid(self):
        result = translator.track_to_mpd_format(
            TlTrack(2, Track()), position=1)
        self.assertIn(('Pos', 1), result)
        self.assertIn(('Id', 2), result)

    def test_track_to_mpd_format_for_nonempty_track(self):
        result = translator.track_to_mpd_format(
            TlTrack(122, self.track), position=9)
        self.assertIn(('file', 'a uri'), result)
        self.assertIn(('Time', 137), result)
        self.assertIn(('Artist', 'an artist'), result)
        self.assertIn(('Title', 'a name'), result)
        self.assertIn(('Album', 'an album'), result)
        self.assertIn(('AlbumArtist', 'an other artist'), result)
        self.assertIn(('Composer', 'a composer'), result)
        self.assertIn(('Performer', 'a performer'), result)
        self.assertIn(('Genre', 'a genre'), result)
        self.assertIn(('Track', '7/13'), result)
        self.assertIn(('Date', '1977-01-01'), result)
        self.assertIn(('Disc', 1), result)
        self.assertIn(('Pos', 9), result)
        self.assertIn(('Id', 122), result)
        self.assertNotIn(('Comment', 'a comment'), result)
        self.assertEqual(len(result), 14)

    def test_track_to_mpd_format_musicbrainz_trackid(self):
        track = self.track.replace(musicbrainz_id='foo')
        result = translator.track_to_mpd_format(track)
        self.assertIn(('MUSICBRAINZ_TRACKID', 'foo'), result)

    def test_track_to_mpd_format_musicbrainz_albumid(self):
        album = self.track.album.replace(musicbrainz_id='foo')
        track = self.track.replace(album=album)
        result = translator.track_to_mpd_format(track)
        self.assertIn(('MUSICBRAINZ_ALBUMID', 'foo'), result)

    def test_track_to_mpd_format_musicbrainz_albumartistid(self):
        artist = list(self.track.artists)[0].replace(musicbrainz_id='foo')
        album = self.track.album.replace(artists=[artist])
        track = self.track.replace(album=album)
        result = translator.track_to_mpd_format(track)
        self.assertIn(('MUSICBRAINZ_ALBUMARTISTID', 'foo'), result)

    def test_track_to_mpd_format_musicbrainz_artistid(self):
        artist = list(self.track.artists)[0].replace(musicbrainz_id='foo')
        track = self.track.replace(artists=[artist])
        result = translator.track_to_mpd_format(track)
        self.assertIn(('MUSICBRAINZ_ARTISTID', 'foo'), result)

    def test_concat_multi_values(self):
        artists = [Artist(name='ABBA'), Artist(name='Beatles')]
        translated = translator.concat_multi_values(artists, 'name')
        self.assertEqual(translated, 'ABBA;Beatles')

    def test_concat_multi_values_artist_with_no_name(self):
        artists = [Artist(name=None)]
        translated = translator.concat_multi_values(artists, 'name')
        self.assertEqual(translated, '')

    def test_concat_multi_values_artist_with_no_musicbrainz_id(self):
        artists = [Artist(name='Jah Wobble')]
        translated = translator.concat_multi_values(artists, 'musicbrainz_id')
        self.assertEqual(translated, '')

    def test_track_to_mpd_format_with_stream_title(self):
        result = translator.track_to_mpd_format(self.track, stream_title='foo')
        self.assertIn(('Name', 'a name'), result)
        self.assertIn(('Title', 'foo'), result)

    def test_track_to_mpd_format_with_empty_stream_title(self):
        result = translator.track_to_mpd_format(self.track, stream_title='')
        self.assertIn(('Name', 'a name'), result)
        self.assertIn(('Title', ''), result)

    def test_track_to_mpd_format_with_stream_and_no_track_name(self):
        track = self.track.replace(name=None)
        result = translator.track_to_mpd_format(track, stream_title='foo')
        self.assertNotIn(('Name', ''), result)
        self.assertIn(('Title', 'foo'), result)


class PlaylistMpdFormatTest(unittest.TestCase):

    def test_mpd_format(self):
        playlist = Playlist(tracks=[
            Track(track_no=1), Track(track_no=2), Track(track_no=3)])
        result = translator.playlist_to_mpd_format(playlist)
        self.assertEqual(len(result), 3)

    def test_mpd_format_with_range(self):
        playlist = Playlist(tracks=[
            Track(track_no=1), Track(track_no=2), Track(track_no=3)])
        result = translator.playlist_to_mpd_format(playlist, 1, 2)
        self.assertEqual(len(result), 1)
        self.assertEqual(dict(result[0])['Track'], 2)
