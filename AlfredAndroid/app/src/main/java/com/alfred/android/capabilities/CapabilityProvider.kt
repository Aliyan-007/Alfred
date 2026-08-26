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
import com.alfred.android.capabilities.shortcuts.ShortcutCapability
import com.alfred.android.capabilities.volume.HardwareCapability
import com.alfred.android.capabilities.volume.VolumeCapability

object CapabilityProvider {
    fun populate(registry: CapabilityRegistry) {
        registry.register(BatteryCapability())
        registry.register(DeviceInfoCapability())
        registry.register(AppCapability())
        registry.register(UrlCapability())
        registry.register(MediaCapability())
        registry.register(VolumeCapability())
        registry.register(HardwareCapability())
        registry.register(NotificationCapability())
        registry.register(CalendarCapability())
        registry.register(AlarmCapability())
        registry.register(ClipboardCapability())
        registry.register(ShortcutCapability())
        registry.register(AccessibilityCapability())
    }
}
