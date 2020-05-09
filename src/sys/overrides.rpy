python:
    """
    Overrides

    These are the few areas we intentionally override names.
    We have to replace the main menu.
    We also switch around a few key bindings.

    """


init offset = 1

init python:
    config.keymap['game_menu'].remove('mouseup_3')
    config.keymap['hide_windows'].append('mouseup_3')
    config.keymap['trickster'] = []
    config.keymap['trickster'].append('ctrl_K_t')
    config.keymap['trickster'].append('alt_K_t')
    config.keymap['trickster'].append('shift_K_t')

    # renpy.loader.auto_mtimes.clear()
    # renpy.loader.add_auto(os.path.abspath("autoreload"), force=True)
    # renpy.config.autoreload_blacklist.append("")
    # with renpy.loader.auto_lock:
    #     renpy.loader.auto_mtimes[fn]

define config.autoreload = False

transform menustill:
    xpos 20

# This doesn't really get used now, because main_menu from the liteskin takes over
screen main_menu():
    tag menu

    style_prefix "main_menu"

    add "titlesky"

    # Pesterquest originally used an animation here, but now
    # uses a prerendered video file. 

    #add "gui/sun2.png" at titlesun
    #add "gui/lensflare.png" at titleflare
    #add "gui/clouds.png" at titleclouds
    add "gui/title_noglitch" pos(5, 5) at title

    #imagebutton auto "gui/title_%s.png" action NullAction() pos (5, 5)

    vbox:
        xpos 20
        xanchor 0
        yalign 1.0

        imagebutton auto "gui/start_%s.png" ysize 60 action ShowVolSelectAction at menumove
        imagebutton auto "{{assets}}/start_fanon_%s.png" ysize 60 action ShowMenuFallback("start_custom", "start") alternate (lambda: renpy.play("music/honk_short.wav")) at menumove
        imagebutton auto "gui/load_%s.png" ysize 60 action ShowMenu('load') at menumove
        imagebutton auto "gui/options_%s.png" ysize 60 action ShowMenu('preferences') at menumove
        hbox:
            imagebutton auto "gui/friends_%s.png" ysize 60 action ShowMenu("achievements") at menustill
            imagebutton auto "{{assets}}/dlc_superscript_%s.png" ysize 60 action ShowMenu("dlc_achievements") at menustill
        hbox:
            imagebutton auto "gui/credits_%s.png" ysize 60 action ShowMenu("about") at menustill
            imagebutton auto "{{assets}}/dlc_superscript_%s.png" ysize 60 action ShowMenu("credits") at menustill
        imagebutton auto "gui/exit_%s.png" ysize 60 action Quit(confirm=not main_menu) at menumove

    # use mainmenu_devbox
    key "trickster" action getMousePosition, ShowMenu("mainmenu_devbox")


## Navigation screen ###########################################################
##
## This screen is included in the main and game menus, and provides navigation
## to other menus, and to start the game.

screen navigation():
    vbox:
        style_prefix "navigation"
        xpos gui.navigation_xpos
        yalign 0.5
        spacing gui.navigation_spacing
        
        if not main_menu:
            textbutton _("History") action ShowMenuFallback("history")
            textbutton _("Save") action ShowMenuFallback("save")
        textbutton _("Load") action ShowMenuFallback("load")
        textbutton _("Options") action ShowMenuFallback("preferences")
        if _in_replay:
            textbutton _("End Replay") action EndReplay(confirm=True)
        elif not main_menu:
            textbutton _("Main Menu") action MainMenu()

        textbutton _("Volume Select") action ShowMenuFallback("vol_select_custom", "vol_select")

        for label, screen in [
            ("Achievements (PQ)", "achievements"),
            ("Achievements", "dlc_achievements"),
            ("Credits (PQ)", "about"),
            ("Credits", "credits"),
            ("Warnings (PQ)", "content_warnings"),
            ("Warnings", "dlc_warnings"),
        ]:
            if renpy.has_screen(screen):
                textbutton _(label) action ShowMenuFallback(screen)

        textbutton _("Close Menu") action Return()


## Preferences screen ##########################################################
##
## The preferences screen allows the player to configure the game to better suit
## themselves.
##
## https://www.renpy.org/doc/html/screen_special.html#preferences

# Set defaults
$ gui.preference("fse_clickytags", False)

screen preferences():
    tag menu
    use game_menu(_("Options"), scroll="viewport"):
        vbox:
            hbox:
                box_wrap True
                if renpy.variant("pc"):
                    vbox:
                        style_prefix "radio"
                        label _("Display")
                        textbutton _("Window") action Preference("display", "window")
                        textbutton _("Fullscreen") action Preference("display", "fullscreen")

                vbox:
                    style_prefix "radio"
                    label _("Rollback Side")
                    textbutton _("Disable") action Preference("rollback side", "disable")
                    textbutton _("Left") action Preference("rollback side", "left")
                    textbutton _("Right") action Preference("rollback side", "right")

                vbox:
                    style_prefix "check"
                    label _("Skip")
                    textbutton _("Unseen Text") action Preference("skip", "toggle")
                    textbutton _("After Choices") action Preference("after choices", "toggle")
                    textbutton _("Transitions") action InvertSelected(Preference("transitions", "toggle"))

                vbox:
                    style_prefix "check"
                    label "Hashtags"
                    textbutton _("Click to advance") action gui.TogglePreference("fse_clickytags", True, False)

            hbox:
                box_wrap True
                ## Additional vboxes of type "radio_pref" or "check_pref" can be
                ## added here, to add additional creator-defined preferences.vbox:

                vbox:
                    style_prefix "radio"
                    label _("Flashing Lights")
                    textbutton _("Enabled") action SetField(persistent, 'flash', True)
                    textbutton _("Disabled") action SetField(persistent, 'flash', False)

                # Todo: High contrast text
                # Todo: Quirks on/off
                

            null height (4 * gui.pref_spacing)
            hbox:
                style_prefix "slider"
                box_wrap True

                vbox:
                    label _("Text Speed")
                    bar value Preference("text speed")
                    label _("Auto-Forward Time")
                    bar value Preference("auto-forward time")

                vbox:
                    label _("Music Volume")
                    hbox:
                        bar value Preference("music volume")

                    label _("Sound Volume")
                    hbox:
                        bar value Preference("sound volume")
                        if config.sample_sound:
                            textbutton _("Test") action Play("sound", config.sample_sound)

                    null height gui.pref_spacing
                    textbutton _("Mute All"):
                        action Preference("all mute", "toggle")
                        style "mute_all_button"