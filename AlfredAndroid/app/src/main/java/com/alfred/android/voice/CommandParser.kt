package com.alfred.android.voice

class CommandParser {

    fun parse(spokenText: String): List<CommandIntent> {

        val normalized = normalize(spokenText)

        if (normalized.isBlank()) {
            return listOf(CommandIntent.Unknown(spokenText))
        }

        val parts = splitMultipleCommands(normalized)

        return parts.mapNotNull { parseSingle(it, spokenText) }
            .ifEmpty {
                listOf(CommandIntent.Unknown(spokenText))
            }
    }

    private fun parseSingle(
        command: String,
        originalText: String
    ): CommandIntent? {

        // ---------------------------------------------
        // BATTERY
        // ---------------------------------------------

        if (containsAny(command, listOf(
                "battery",
                "battery kitni",
                "battery kitna",
                "battery percentage",
                "battery percent",
                "battery level",
                "charge kitna",
                "charge kitni",
                "phone charge",
                "phone ki battery",
                "kitni battery",
                "kitna charge",
                "battery batao",
                "battery btao",
                "charge batao",
                "charge btao",
                "meri battery kitni hai"
            ))) {
            return CommandIntent.Battery
        }

        // ---------------------------------------------
        // FLASHLIGHT
        // ---------------------------------------------

        if (containsAny(command, listOf(
                "flashlight off",
                "flashlight band",
                "flashlight bandh",
                "torch off",
                "torch band",
                "torch bandh",
                "light off",
                "light band",
                "light bandh",
                "flash off",
                "flash band",
                "flash bandh"
            ))) {
            return CommandIntent.Flashlight(false)
        }

        if (containsAny(command, listOf(
                "flashlight on",
                "flashlight chalao",
                "flashlight jalao",
                "flashlight kholo",
                "flashlight chalu",
                "torch on",
                "torch chalao",
                "torch jalao",
                "torch kholo",
                "torch chalu",
                "torch laga do",
                "light on",
                "light chalao",
                "light jalao",
                "light kholo",
                "light chalu",
                "flash on",
                "flash chalao"
            ))) {
            return CommandIntent.Flashlight(true)
        }

        // ---------------------------------------------
        // VOLUME WITH OPTIONAL NUMBER
        // ---------------------------------------------

        parseVolume(command)?.let {
            return it
        }

        // ---------------------------------------------
        // SETTINGS
        // ---------------------------------------------

        if (containsAny(command, listOf(
                "open settings",
                "settings kholo",
                "settings khol",
                "settings open",
                "settings chalao",
                "phone settings",
                "phone ki settings",
                "setting kholo",
                "setting khol",
                "setting open",
                "settings khol do",
                "setting khol do"
            ))) {
            return CommandIntent.OpenSettings
        }

        // ---------------------------------------------
        // YOUTUBE SEARCH
        // ---------------------------------------------

        extractAfterAny(
            command,
            listOf(
                "youtube par search karo",
                "youtube pe search karo",
                "youtube par search",
                "youtube pe search",
                "youtube search karo",
                "youtube search",
                "youtube par",
                "youtube pe"
            )
        )?.let { query ->
            if (query.isNotBlank()) {
                return CommandIntent.YouTubeSearch(cleanQuery(query))
            }
        }

        // "youtube kholo aur search karo spider man"
        if (command.contains("youtube") &&
            (command.contains("search karo") ||
             command.contains("search") ||
             command.contains("talash karo") ||
             command.contains("dhundo"))) {

            val query = extractSearchQuery(command)
            if (query.isNotBlank()) {
                return CommandIntent.YouTubeSearch(query)
            }
        }

        // ---------------------------------------------
        // GOOGLE / WEB SEARCH
        // ---------------------------------------------

        extractAfterAny(
            command,
            listOf(
                "google par search karo",
                "google pe search karo",
                "google search karo",
                "google par search",
                "google pe search",
                "search karo",
                "search"
            )
        )?.let { query ->
            if (query.isNotBlank()) {
                return CommandIntent.WebSearch(cleanQuery(query))
            }
        }

        // ---------------------------------------------
        // SPOTIFY SEARCH
        // ---------------------------------------------

        extractAfterAny(
            command,
            listOf(
                "spotify par search karo",
                "spotify pe search karo",
                "spotify search karo",
                "spotify par search",
                "spotify pe search"
            )
        )?.let { query ->
            if (query.isNotBlank()) {
                return CommandIntent.SpotifySearch(cleanQuery(query))
            }
        }

        // ---------------------------------------------
        // WHATSAPP SHARE
        // ---------------------------------------------

        extractAfterAny(
            command,
            listOf(
                "whatsapp par message karo",
                "whatsapp pe message karo",
                "whatsapp par message",
                "whatsapp pe message",
                "whatsapp message"
            )
        )?.let { message ->
            if (message.isNotBlank()) {
                return CommandIntent.WhatsAppShare(cleanQuery(message))
            }
        }

        // ---------------------------------------------
        // SIMPLE APP OPEN
        // ---------------------------------------------

        if (containsAny(command, listOf(
                "open youtube",
                "youtube kholo",
                "youtube khol",
                "youtube open",
                "youtube chalao",
                "youtube chala",
                "youtube start",
                "youtube khol do"
            ))) {
            return CommandIntent.OpenApp(CommandIntent.App.YOUTUBE)
        }

        if (containsAny(command, listOf(
                "open whatsapp",
                "whatsapp kholo",
                "whatsapp khol",
                "whatsapp open",
                "whatsapp chalao",
                "whatsapp chala",
                "whatsapp start",
                "whatsapp khol do"
            ))) {
            return CommandIntent.OpenApp(CommandIntent.App.WHATSAPP)
        }

        if (containsAny(command, listOf(
                "open spotify",
                "spotify kholo",
                "spotify khol",
                "spotify open",
                "spotify chalao",
                "spotify chala",
                "spotify start",
                "spotify khol do"
            ))) {
            return CommandIntent.OpenApp(CommandIntent.App.SPOTIFY)
        }

        // ---------------------------------------------
        // GREETING
        // ---------------------------------------------

        if (containsAny(command, listOf(
                "hello",
                "hi",
                "hey",
                "salam",
                "salaam",
                "assalamualaikum",
                "assalamu alaikum",
                "assalam o alaikum"
            ))) {
            return CommandIntent.Greeting
        }

        // ---------------------------------------------
        // HELP
        // ---------------------------------------------

        if (containsAny(command, listOf(
                "help",
                "madad",
                "kya kar sakte ho",
                "tum kya kar sakte ho",
                "aap kya kar sakte ho",
                "kya kya kar sakte ho",
                "commands",
                "command list",
                "commands batao"
            ))) {
            return CommandIntent.Help
        }

        return CommandIntent.Unknown(originalText)
    }

    private fun parseVolume(command: String): CommandIntent.Volume? {

        val up = containsAny(command, listOf(
            "volume up",
            "volume barhao",
            "volume barao",
            "volume increase",
            "volume zyada",
            "volume tez",
            "awaz barhao",
            "awaz barao",
            "awaz badhao",
            "awaz tez karo",
            "sound barhao",
            "sound barao",
            "sound badhao",
            "sound tez karo",
            "loud karo"
        ))

        val down = containsAny(command, listOf(
            "volume down",
            "volume kam",
            "volume kam karo",
            "volume decrease",
            "volume ghatao",
            "awaz kam",
            "awaz kam karo",
            "awaz ghatao",
            "awaz dheemi karo",
            "sound kam",
            "sound kam karo",
            "sound ghatao",
            "sound dheemi karo",
            "quiet karo"
        ))

        if (!up && !down) return null

        val number = Regex("""\b(\d{1,3})\b""")
            .find(command)
            ?.groupValues
            ?.getOrNull(1)
            ?.toIntOrNull()
            ?.coerceIn(1, 100)

        return if (up) {
            CommandIntent.Volume(
                CommandIntent.Volume.Direction.UP,
                number
            )
        } else {
            CommandIntent.Volume(
                CommandIntent.Volume.Direction.DOWN,
                number
            )
        }
    }

    private fun extractSearchQuery(command: String): String {

        var result = command

        listOf(
            "youtube kholo",
            "youtube khol do",
            "youtube open karo",
            "youtube open",
            "youtube chalao",
            "youtube chala",
            "youtube",
            "search karo",
            "search",
            "talash karo",
            "dhundo"
        ).forEach { phrase ->
            result = result.replace(
                phrase,
                " ",
                ignoreCase = true
            )
        }

        return result
            .replace(
                Regex("""\b(aur|phir|please|zara)\b"""),
                " "
            )
            .replace(Regex("\\s+"), " ")
            .trim()
    }

    private fun extractAfterAny(
        command: String,
        phrases: List<String>
    ): String? {

        for (phrase in phrases) {

            val index =
                command.indexOf(
                    phrase,
                    ignoreCase = true
                )

            if (index >= 0) {
                return command
                    .substring(index + phrase.length)
                    .trim()
            }
        }

        return null
    }

    private fun cleanQuery(query: String): String {

        return query
            .trim()
            .replace(
                Regex("""^(please|zara|na|to)\s+"""),
                ""
            )
            .replace(
                Regex("""\s+(please|na|zara)$"""),
                ""
            )
            .replace(
                Regex("\\s+"),
                " "
            )
            .trim()
    }

    private fun splitMultipleCommands(
        command: String
    ): List<String> {

        // Keep "aur" inside search queries unless it clearly
        // separates two actions.
        val parts = mutableListOf<String>()

        val regex = Regex(
            """\s+(?:aur phir|phir|then)\s+"""
        )

        val strongSplit = regex.split(command)

        if (strongSplit.size > 1) {
            parts += strongSplit
            return parts.filter { it.isNotBlank() }
        }

        // Common two-action patterns.
        val markers = listOf(
            " aur torch ",
            " aur flashlight ",
            " aur settings ",
            " aur volume ",
            " aur youtube kholo",
            " aur whatsapp kholo",
            " aur spotify kholo"
        )

        for (marker in markers) {
            val index = command.indexOf(marker)
            if (index > 0) {
                val first = command.substring(0, index)
                val second = command.substring(index + 5)
                return listOf(first, second)
                    .filter { it.isNotBlank() }
            }
        }

        return listOf(command)
    }

    private fun normalize(text: String): String {

        var command = text
            .lowercase()
            .trim()

        command = command
            .replace("assalam o alaikum", "salam")
            .replace("assalamu alaikum", "salam")
            .replace("assalamualaikum", "salam")
            .replace("al salam alaikum", "salam")

        command = command.replace(
            Regex("""[,\.?!:;]"""),
            " "
        )

        val wakeWords = listOf(
            "hey alfred",
            "hello alfred",
            "hi alfred",
            "oye alfred",
            "ok alfred",
            "okay alfred",
            "alfred",
            "hey friday",
            "hello friday",
            "hi friday",
            "oye friday",
            "ok friday",
            "okay friday",
            "friday"
        )

        wakeWords
            .sortedByDescending { it.length }
            .forEach { wakeWord ->
                command = command.replace(
                    wakeWord,
                    " "
                )
            }

        command = command
            .replace("karo na", "karo")
            .replace("kr do", "karo")
            .replace("krdo", "karo")
            .replace("kardo", "karo")
            .replace("kar do", "karo")
            .replace("kholo na", "kholo")
            .replace("khol do", "kholo")
            .replace("kholna", "kholo")
            .replace("chala do", "chalao")
            .replace("chalao na", "chalao")
            .replace("jala do", "jalao")
            .replace("bata do", "batao")
            .replace("btao", "batao")
            .replace("btana", "batao")

        return command
            .replace(Regex("\\s+"), " ")
            .trim()
    }

    private fun containsAny(
        command: String,
        keywords: List<String>
    ): Boolean {
        return keywords.any {
            command.contains(
                it,
                ignoreCase = true
            )
        }
    }
}
