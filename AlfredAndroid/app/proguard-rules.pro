-keepattributes *Annotation*, InnerClasses, Signature
-dontnote kotlinx.serialization.**
-dontwarn com.google.errorprone.annotations.**
-keepclassmembers class **$$serializer { *; }
-keepclasseswithmembers class com.alfred.android.** {
    kotlinx.serialization.KSerializer serializer(...);
}
-keep,includedescriptorclasses class com.alfred.android.**$$serializer { *; }
