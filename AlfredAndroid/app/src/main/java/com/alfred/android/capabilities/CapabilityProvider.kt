package com.alfred.android.capabilities

import com.alfred.android.capabilities.accessibility.AccessibilityCapability
import com.alfred.android.capabilities.alarms.AlarmCapability
import com.alfred.android.capabilities.apps.AppCapability
import com.alfred.android.capabilities.apps.UrlCapability
import com.alfred.android.capabilities.battery.BatteryCapability
import com.alfred.android.capabilities.battery.DeviceInfoCapability
import com.alfred.android.capabilities.calendar.CalendarCapability
import com.alfred.android.capabilities.clipboard.ClipboardCapability
import com.alfred.android.capabilities.media.MediaCapability
import com.alfred.android.capabilities.notifications.NotificationCapability
import com.alfred.android.capabilities.phone.PhoneCapability
import com.alfred.android.capabilities.settings.SettingsCapability
import com.alfred.android.capabilities.shortcuts.ShortcutCapability
import com.alfred.android.capabilities.volume.HardwareCapability
import com.alfred.android.capabilities.volume.VolumeCapability


object CapabilityProvider {

    fun populate(
        registry: CapabilityRegistry
    ) {

        // Battery
        registry.register(
            BatteryCapability()
        )

        // Device information
        registry.register(
            DeviceInfoCapability()
        )

        // Open and list applications
        registry.register(
            AppCapability()
        )

        // Open websites and URLs
        registry.register(
            UrlCapability()
        )

        // Phone, dialer and SMS
        registry.register(
            PhoneCapability()
        )

        // Media controls
        registry.register(
            MediaCapability()
        )

        // Volume controls
        registry.register(
            VolumeCapability()
        )

        // Flashlight, vibration and hardware
        registry.register(
            HardwareCapability()
        )

        // Android system settings
        registry.register(
            SettingsCapability()
        )

        // Notifications
        registry.register(
            NotificationCapability()
        )

        // Calendar
        registry.register(
            CalendarCapability()
        )

        // Alarms
        registry.register(
            AlarmCapability()
        )

        // Clipboard
        registry.register(
            ClipboardCapability()
        )

        // Custom shortcuts and workflows
        registry.register(
            ShortcutCapability()
        )

        // Accessibility controls
        registry.register(
            AccessibilityCapability()
        )
    }
}
