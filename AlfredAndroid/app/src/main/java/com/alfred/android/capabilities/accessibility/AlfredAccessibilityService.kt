package com.alfred.android.capabilities.accessibility

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.graphics.Path
import android.os.Build
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import com.alfred.android.util.Logger

class AlfredAccessibilityService : AccessibilityService() {
    private val tag = "ALFRED-A11y"

    override fun onServiceConnected() { super.onServiceConnected(); AccessibilityState.connected = true; Logger.i(tag, "connected") }
    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}
    override fun onInterrupt() {}
    override fun onDestroy() { AccessibilityState.connected = false; super.onDestroy() }

    fun doBack(): Boolean = performGlobalAction(GLOBAL_ACTION_BACK)
    fun doHome(): Boolean = performGlobalAction(GLOBAL_ACTION_HOME)
    fun doRecents(): Boolean = performGlobalAction(GLOBAL_ACTION_RECENTS)

    fun tap(x: Float, y: Float): Boolean {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) return false
        val path = Path().apply { moveTo(x, y) }
        return dispatchGesture(GestureDescription.Builder().addStroke(GestureDescription.StrokeDescription(path, 0L, 50L)).build(), null, null)
    }

    fun swipe(x1: Float, y1: Float, x2: Float, y2: Float, dur: Long = 300L): Boolean {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) return false
        val path = Path().apply { moveTo(x1, y1); lineTo(x2, y2) }
        return dispatchGesture(GestureDescription.Builder().addStroke(GestureDescription.StrokeDescription(path, 0L, dur)).build(), null, null)
    }

    fun clickByText(text: String): Boolean {
        val root = rootInActiveWindow ?: return false
        val matches = root.findAccessibilityNodeInfosByText(text)
        val target = matches.firstOrNull { it.isVisibleToUser && it.isEnabled } ?: return false
        return if (target.isClickable) target.performAction(AccessibilityNodeInfo.ACTION_CLICK)
        else {
            var node = target.parent
            while (node != null) { if (node.isClickable && node.isVisibleToUser) return node.performAction(AccessibilityNodeInfo.ACTION_CLICK); node = node.parent }
            false
        }
    }

    companion object { @Volatile var instance: AlfredAccessibilityService? = null }
    init { instance = this }
}

object AccessibilityState { @Volatile var connected: Boolean = false }
