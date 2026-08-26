package com.alfred.android.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.dp
import com.alfred.android.ui.theme.AlfredPrimary
import com.alfred.android.ui.theme.AlfredSurfaceVariant

@Composable
fun AlfredLogo(modifier: Modifier = Modifier) {
    Surface(modifier = modifier.size(72.dp), shape = RoundedCornerShape(20.dp), color = AlfredSurfaceVariant) {
        Box(contentAlignment = Alignment.Center) {
            Canvas(Modifier.size(44.dp)) {
                val s = Stroke(width = 4.dp.toPx())
                val p = Path().apply {
                    moveTo(size.width * 0.5f, 0f); lineTo(size.width, size.height)
                    lineTo(size.width * 0.82f, size.height); lineTo(size.width * 0.66f, size.height * 0.62f)
                    lineTo(size.width * 0.34f, size.height * 0.62f); lineTo(size.width * 0.18f, size.height)
                    lineTo(0f, size.height); close()
                }
                drawPath(p, color = AlfredPrimary, style = s)
                drawLine(AlfredPrimary, Offset(size.width * 0.42f, size.height * 0.42f),
                    Offset(size.width * 0.58f, size.height * 0.42f), strokeWidth = 4.dp.toPx())
            }
        }
    }
}
