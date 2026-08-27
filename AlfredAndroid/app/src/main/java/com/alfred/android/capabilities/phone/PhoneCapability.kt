package com.alfred.android.capabilities.phone

import android.content.Context
import android.content.Intent
import android.net.Uri

import com.alfred.android.capabilities.BaseCapability
import com.alfred.android.capabilities.CapabilityState
import com.alfred.android.protocol.Command
import com.alfred.android.protocol.CommandError
import com.alfred.android.protocol.CommandResult
import com.alfred.android.protocol.ErrorCodes

import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.jsonPrimitive


class PhoneCapability : BaseCapability() {

    override val id = "phone"

    override val displayName = "Phone"


    override fun refresh(
        context: Context
    ) {

        setState(
            CapabilityState.AVAILABLE
        )
    }


    override suspend fun handle(
        command: Command,
        context: Context
    ): CommandResult {

        val action =
            command.action
                .substringAfter(
                    ".",
                    "dial"
                )
                .lowercase()


        return when (action) {

            "dial" ->
                openDialer(
                    command,
                    context
                )

            "call" ->
                callNumber(
                    command,
                    context
                )

            "sms",
            "message" ->
                openSms(
                    command,
                    context
                )

            else ->
                CommandResult.failure(
                    command.id,
                    CommandError(
                        ErrorCodes.UNSUPPORTED_ACTION,
                        "Unknown phone action: $action",
                        id
                    )
                )
        }
    }


    private fun getNumber(
        command: Command
    ): String? {

        return command.parameters[
            "number"
        ]
            ?.jsonPrimitive
            ?.content
            ?.trim()
            ?.takeIf {
                it.isNotBlank()
            }
    }


    private fun openDialer(
        command: Command,
        context: Context
    ): CommandResult {

        val number =
            getNumber(
                command
            )


        val intent =
            Intent(
                Intent.ACTION_DIAL
            )


        if (
            number != null
        ) {

            intent.data =
                Uri.parse(
                    "tel:$number"
                )
        }


        intent.addFlags(
            Intent.FLAG_ACTIVITY_NEW_TASK
        )


        return try {

            context.startActivity(
                intent
            )


            CommandResult.success(
                command.id,
                buildJsonObject {

                    put(
                        "action",
                        JsonPrimitive(
                            "dial"
                        )
                    )

                    put(
                        "number",
                        JsonPrimitive(
                            number ?: ""
                        )
                    )
                }
            )

        } catch (
            error: Throwable
        ) {

            CommandResult.failure(
                command.id,
                CommandError(
                    ErrorCodes.INTERNAL_ERROR,
                    error.message
                        ?: "Failed to open dialer",
                    id
                )
            )
        }
    }


    private fun callNumber(
        command: Command,
        context: Context
    ): CommandResult {

        val number =
            getNumber(
                command
            )
                ?: return CommandResult.failure(
                    command.id,
                    CommandError(
                        ErrorCodes.INVALID_PARAMETERS,
                        "number is required",
                        id
                    )
                )


        /*
         * We intentionally use ACTION_DIAL here.
         *
         * This allows ALFRED to prepare the call
         * without requiring CALL_PHONE permission
         * or silently placing calls.
         */

        val intent =
            Intent(
                Intent.ACTION_DIAL,
                Uri.parse(
                    "tel:$number"
                )
            )


        intent.addFlags(
            Intent.FLAG_ACTIVITY_NEW_TASK
        )


        return try {

            context.startActivity(
                intent
            )


            CommandResult.success(
                command.id,
                buildJsonObject {

                    put(
                        "action",
                        JsonPrimitive(
                            "call"
                        )
                    )

                    put(
                        "number",
                        JsonPrimitive(
                            number
                        )
                    )

                    put(
                        "dialer_opened",
                        JsonPrimitive(
                            true
                        )
                    )
                }
            )

        } catch (
            error: Throwable
        ) {

            CommandResult.failure(
                command.id,
                CommandError(
                    ErrorCodes.INTERNAL_ERROR,
                    error.message
                        ?: "Failed to open dialer",
                    id
                )
            )
        }
    }


    private fun openSms(
        command: Command,
        context: Context
    ): CommandResult {

        val number =
            getNumber(
                command
            )


        val text =
            command.parameters[
                "text"
            ]
                ?.jsonPrimitive
                ?.content
                ?: ""


        val uri =
            if (
                number.isNullOrBlank()
            ) {

                Uri.parse(
                    "smsto:"
                )

            } else {

                Uri.parse(
                    "smsto:$number"
                )
            }


        val intent =
            Intent(
                Intent.ACTION_SENDTO,
                uri
            )


        intent.putExtra(
            "sms_body",
            text
        )


        intent.addFlags(
            Intent.FLAG_ACTIVITY_NEW_TASK
        )


        return try {

            context.startActivity(
                intent
            )


            CommandResult.success(
                command.id,
                buildJsonObject {

                    put(
                        "action",
                        JsonPrimitive(
                            "sms"
                        )
                    )

                    put(
                        "opened",
                        JsonPrimitive(
                            true
                        )
                    )
                }
            )

        } catch (
            error: Throwable
        ) {

            CommandResult.failure(
                command.id,
                CommandError(
                    ErrorCodes.INTERNAL_ERROR,
                    error.message
                        ?: "Failed to open SMS",
                    id
                )
            )
        }
    }
}
