# Alfred Smart Command Phase

## Files

Copy these files into:

app/src/main/java/com/alfred/android/voice/

- CommandIntent.kt
- CommandParser.kt
- LocalCommandProcessor.kt

Replace the existing LocalCommandProcessor.kt with the supplied version.

## Features

1. Roman Urdu normalization
2. Wake-word removal for Alfred and Friday
3. Battery commands
4. Flashlight on/off
5. Volume up/down
6. Numeric volume steps
7. Settings
8. YouTube open
9. YouTube voice search
10. Google/web search
11. Spotify open
12. Spotify search
13. WhatsApp open
14. WhatsApp text sharing
15. Greetings
16. Help
17. Basic multi-command splitting

Examples:

"Alfred YouTube kholo aur search karo Spider-Man"

"Alfred YouTube par Spider-Man search karo"

"Alfred Google par search karo Pakistan weather"

"Alfred Spotify par search karo Arijit Singh"

"Alfred volume 3 barhao"

"Alfred torch on karo"

"Alfred battery batao"

Important:
- WhatsApp contact-specific messaging is NOT implemented yet. The current WhatsApp feature prepares a text message using Android's share chooser. Contact selection/Contacts integration is the next stage.
- Multi-command parsing is intentionally conservative so that "aur" inside a search query is not blindly treated as a separator.

## Build

From D:\alfred\AlfredAndroid:

.\gradlew.bat --stop
.\gradlew.bat assembleDebug

The Kotlin daemon warning you previously saw can fall back to non-daemon compilation. If the build says BUILD SUCCESSFUL, that warning is not the blocking issue.

## Next step

After this build works on the phone, test the command matrix below.

### Required tests

1. Alfred battery batao
2. Alfred torch on karo
3. Alfred torch off karo
4. Alfred volume 3 barhao
5. Alfred volume 2 kam karo
6. Alfred YouTube kholo
7. Alfred YouTube kholo aur search karo Spider-Man
8. Alfred YouTube par search karo Spider-Man
9. Alfred Google par search karo Spider-Man
10. Alfred Spotify par search karo Arijit Singh
11. Alfred WhatsApp kholo
12. Alfred WhatsApp message hello Sir

Then the next engineering step is:
CommandIntent -> CommandParser -> LocalCommandProcessor -> Contacts/WhatsApp integration.

After that:
- contact-name resolution
- "Ali ko message karo..."
- call/contact actions
- music playback actions
- richer multi-step commands
- optional LLM fallback for commands the deterministic parser cannot understand
