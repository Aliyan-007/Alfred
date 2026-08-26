package com.alfred.android.capabilities

enum class CapabilityState(val wireValue: String) {
    AVAILABLE("available"),
    PERMISSION_REQUIRED("permission_required"),
    UNSUPPORTED("unsupported"),
    DISABLED("disabled"),
    UNAVAILABLE("unavailable");
}
