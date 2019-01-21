<h1>Pseudo Bot</h1>

This repository contains the code used in the [**Halite III**](https://halite.io/) competition using Python. I got to know about the competition from [Sentdex](https://github.com/Sentdex/) from his [Youtube](https://www.youtube.com/sentdex) Channel.

Halite III is a resource management game in which players build and command ships that explore the ocean and collect halite. Ships use halite as an energy source, and the player with the most stored halite at the end of the game is the winner.

Players begin play with a shipyard, and can use collected halite to build new ships. To efficiently collect halite, players must devise a strategy based on building ships and dropoff points. Ships can explore the ocean, collect halite, and store it in the shipyard or in dropoff points. Players interact by seeking inspiring competition, or by colliding ships to send both to the bottom of the sea.

***

<h2>Some important rules that were taken into consideration:</h2>

- [x] The decisions for all the ships needed to be within 2 seconds. (otherwise your bot will timeout and lose the game)

- [x] Each ship can only take one decision per turn. (otherwise the game would throw an error and lose the game)

***

* <h1>Running the Game locally.</h1>

* * <h2>On Windows</h2>

  `halite.exe --replay-directory replays/ -vvv --width 64 --height 64 "python PseudoBot.py" "python PseudoBot.py"`

* * <h2>On Linux</h2>

  #TODO

* <h1>Viewing the game visually.</h1>

  drag and drop the `.hlt` file under `replays` folder in [here.](https://halite.io/watch-games)

***

<h1>Explaination of how the Pseudo Bot was designed:</h1>

* Short version:

  As ships are generated from the Shipyard. Each ship scans an area of 8x8 grid from its current position (i.e. from -4 to +4 in both x and y keeping ship's position on the game map as origin) get the maximum resource co-ordinate from that grid and make the ship move towards that target.

* Long version:

  #TODO

***


<h2>Few Strategies I wanted to implement</h2>

- [ ] Implement a drop-off location strategy by scanning 4x4 grid of the whole map with a stride of one. Select random points of top 3 mean scores from those grids.

- [ ] Implement a strtegy such that ships will go back to the position as they change state from "Returning" to "Exploring".

***

<h2>Things that didn't work</h2>

- [x] ~~Scan the whole map once per turn and give ships a maximum resource co-ordinates while iterating over ships that would increase over score.~~
- [x] ~~Randomly assign the size of ship's scanning area.~~


***

<h1>References:</h1>

* [Sentdex](https://www.youtube.com/sentdex)

* [Halite Forums](https://forums.halite.io/)


Thanks to Two Sigma for hosting the competition.
