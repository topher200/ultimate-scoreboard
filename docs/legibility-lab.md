# Legibility Lab

We ran the legibility lab on a real field to find the colors, font, and layout that people can read from across the field. This page records each round and what it decided, so we don't need to test those things again.

## Results so far

| Decision | Winner | Round |
|---|---|---|
| Score font | Terminal font at 2x, drawn bold | 2, 4 |
| Layout | Team names on top, the matchup label ("W"/"1") stacked between the scores | 3 |
| Team colors | Yellow left, white right, on black | 3, 4 |
| Team name brightness | 2/3 | 4 |
| WMP indicator | 3 px cyan dashed frame at full brightness that marches for 30 s after each point | 2, 3, 4, 5 |
| MMP indicator | No frame | 5 |
| Matchup label color | Cyan for WMP, magenta for MMP | 5 |
| MMP layout | Same places as WMP, with the timing dots 1 row above the bottom edge | 6, 7 |
| Team names near the WMP frame | The frame stays dark within 1 px of each letter | 8 |

The scoreboard uses all of these. Its colors are yellow and white for the teams, cyan for WMP, and magenta for the MMP label: yellow, cyan, and magenta are the three printer primaries, and each looks unlike the others. The timing dots are white, like the right team; that is a known compromise.

## What we learned

- **Ask a question that decides something.** A vote that asks whether two screens look different is wasted: the simulator already shows that. Each vote should pick between real candidates for an open decision.
- **A/B beats ratings for close calls.** Good/OK/Bad ratings sorted out bad colors quickly. To pick between good candidates, switch between A and B and vote for one.
- **The board has 4 levels per color channel.** The matrix runs at `bit_depth=2`, so each channel is off, 1/3, 2/3, or full. Other levels, such as 3/4, need a higher bit depth.
- **Character size limits the range.** The score digits are 16 LEDs tall. For a much longer range, the digits need more LEDs or a bigger panel pitch.
- **Thin lines disappear at a distance.** A 1 px frame was almost invisible. Thick strokes and a 3 px frame showed up well.
- **Motion helps a frame.** A marching frame beat a static, blinking, or pulsing one.

## Rounds

Each round showed "13" and "18" as the scores.

### Round 1: colors, fonts, layouts, and backgrounds (Good/OK/Bad)

- **Colors** (both scores in one color): good = white, yellow; ok = cyan, lime, spring, amber, orange, sky; bad = green, red, magenta, pink, violet, blue.
- **Fonts**: the terminal font at 2x was good; a 5x7 and a 3x5 pixel font were ok.
- **Layouts**: names with no gender indicator were good. A 1 px frame or a 2 px bar along the bottom were too hard to see.
- **Backgrounds**: white digits on navy and maroon halves were good; colored digits on dim backgrounds of the same color, and white on gray, were bad.
- Good/OK/Bad did not work for pairs of team colors, which need a left-vs-right choice.

### Round 2: fonts, gender indicators, and team colors (head to head)

- **Fonts** (one per half): the terminal font at 2x beat 7-segment digits with 3 px and 4 px strokes, and the 5x7 and 3x5 pixel fonts, even though those were taller.
- **Gender indicator**: a 3 px frame beat a 1 px frame, corner blocks, a background tint, blinking, and pulsing. A marching 3 px frame beat a static one.
- **Team colors**: yellow/cyan on black beat white/orange, yellow/sky, white/amber, and white digits on navy/maroon halves. Orange was the worst.

### Round 3: full scoreboard layouts with a 3 px frame

- Names with "W"/"1" stacked between the scores beat the old scoreboard, the same layout without names, and "W1" under the scores.
- White/cyan beat yellow/cyan, and white/yellow beat white/cyan.
- A magenta WMP frame did not show up well.

### Round 4: WMP frame colors and small changes

- **WMP frame color**: good = cyan, sky, lime; ok = magenta, amber, spring, red; bad = orange.
- **WMP against MMP**: every pair we tried was easy to tell apart, so this question decided nothing.
- **Bold scores** beat plain scores.
- **Team names at 2/3 brightness** beat full brightness.
- **A full-brightness frame** beat a frame at 2/3 brightness.
- **Yellow left, white right** beat white left, yellow right.

### Round 5: settle the design

Each pair asked one question.

- **WMP color** ("From the far end zone, which WMP frame do you notice faster?"): cyan beat sky and lime, and lime beat sky. Magenta and pink looked best but were harder to see; white was easiest to see but looked plainer than cyan.
- **MMP indicator** ("For MMP points, which would you rather see all game?"): no frame beat a white frame and an amber frame, and white beat amber.
- **New against old** ("From the far end zone, which score can you read?"): the new design beat the old scoreboard for a WMP point. For an MMP point, the old scoreboard beat the new design with a white frame, which had already lost to no frame.

After round 5, we picked the MMP label color in the simulator: white matched the right team, so the label is magenta.

### Round 6: MMP layout

- **MMP layout** ("For MMP points, which layout looks better?"): the same places as WMP beat a layout that moved the names 2 px into the top corners and the timing dots 2 rows down, into the frame's space.

That pair changed several things at once, so round 7 tests each change by itself.

### Round 7: MMP spacing, one change at a time

Each A/B pair showed today's MMP layout as A and one change as B ("For MMP points, which looks better?"). Then a pair for each layout showed a WMP point and an MMP point, and asked for Good, OK, or Bad.

- **Timing dots 2 rows down**, into the frame's space: B won, and the switch from WMP was the only one rated Good.
- **Names 2 rows up**: A won. The switch was OK.
- **Names 2 px out to the sides**: A won. The switch was Bad.
- **Names 2 rows up and scores 1 row up**: Same. The switch was OK.
- **Team names at full brightness**: A won, so the names stay at 2/3.
- **Today's layout**: the switch was OK.

### Round 8: tall letters and the WMP frame

On the board, the tops of tall letters such as "i" and "l" touched the WMP frame. Each pair showed a WMP point with the names "Flick" and "Bluff", in two of seven layouts ("For WMP points, which looks better? Look where the team names meet the frame."). Every two layouts made a pair.

The votes ranked the layouts in one order, and each layout beat every layout below it:

1. The frame stays dark within 1 px of each letter: 6 wins.
2. The top edge of the frame is 2 px: 5 wins.
3. The names are drawn over the frame: 4 wins.
4. Today's layout: 3 wins.
5. The names 1 row down; a 2 px frame; and everything 1 row down with a 2 px bottom edge: 1 win each.

Moving the names or thinning the whole frame lost to today's layout.

## Run a round

1. Hold both buttons for about 5 seconds. The scores reset at 1 second, and at 5 seconds the board restarts into the lab. Hold both buttons for 5 seconds again to go back to the scoreboard.
2. The board joins Wi-Fi and shows a QR code. Scan it with a phone on the same network. On a field, use a phone hotspot with the Wi-Fi name and password in `settings.toml`.
3. Walk to where viewers will stand, for example the far end zone, in sun if you can.
4. For each pair, tap **Show A** and **Show B** a few times, then answer the question on the page. Vote **Same** when the two are too close to call. A vote moves to the next item.
5. Copy the votes block at the bottom of the page.

The board keeps the votes across reboots. Without Wi-Fi, the left and right buttons step through the items, and holding both for 1 second turns auto-advance on or off. In the lab, the board does not check for updates, so power on normally to get a new round.

## Write a round

1. Write down the decision that is still open and the candidates for it. Leave out candidates that earlier rounds ruled out.
2. In `src/lab_screens.py`, add a function that returns the round's items, and pass it to `Lab` in `run_lab` in `src/lab.py`:
   - A `Pair` shows two screens and asks a question; the viewer votes A, Same, or B. `_round_robin` makes a `Pair` for every two candidates.
   - A `Pair` with `rating=True` shows two screens and asks for Good, OK, or Bad.
   - A `Screen` with `compare=True` shows a different font on each half and asks which half reads better.
   - A plain `Screen` asks for Good, OK, or Bad.
3. Give every item an ID that no earlier round used, so old votes don't match it.
4. Preview it with `just sim-lab`, and run `just test`. The render tests check that no text overlaps the frame or other text.
5. Release it over Wi-Fi with `just release <version>` and `just activate <version>`.
6. Add the round and its results to this page.

The custom screen (Z1) at the end of every round takes a font, colors, frame, and layout from the lab page. It is useful to try an idea before you write a round for it.
