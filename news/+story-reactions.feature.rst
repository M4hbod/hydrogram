``Client.send_reaction`` reacts to stories, via ``story_id``, and accepts custom
emoji ids and lists of reactions as well as a single emoji string. ``Story.react``
depended on the story path and raised ``TypeError`` without it.
