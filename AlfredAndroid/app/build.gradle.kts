import java.util.Properties

fun loadEnvFile(): Properties {
    val envFile = rootProject.projectDir.parentFile.resolve(".env")
    val properties = Properties()

    if (envFile.exists()) {
        envFile.inputStream().use {
            properties.load(it)
        }
    }

    return properties
}

val env = loadEnvFile()

val groqApiKey =
    env.getProperty("GROQ_API_KEY")
        ?: System.getenv("GROQ_API_KEY")
        ?: ""

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.serialization)
}

android {

    namespace = "com.alfred.android"

    compileSdk = 34

    defaultConfig {
        applicationId = "com.alfred.android"

        minSdk = 26

        targetSdk = 34

        versionCode = 1

        versionName = "0.1.0"

        testInstrumentationRunner =
            "androidx.test.runner.AndroidJUnitRunner"

        vectorDrawables {
            useSupportLibrary = true
        }
    }

    buildTypes {

        debug {

            isMinifyEnabled = false

            applicationIdSuffix = ".debug"

            versionNameSuffix = "-debug"

            buildConfigField(
                "String",
                "GROQ_API_KEY",
                "\"${groqApiKey.replace("\"", "\\\"")}\""
            )
        }

        release {

            isMinifyEnabled = true

            isShrinkResources = true

            buildConfigField(
                "String",
                "GROQ_API_KEY",
                "\"${groqApiKey.replace("\"", "\\\"")}\""
            )

            proguardFiles(
                getDefaultProguardFile(
                    "proguard-android-optimize.txt"
                ),
                "proguard-rules.pro"
            )
        }
    }

    compileOptions {
        sourceCompatibility =
            JavaVersion.VERSION_17

        targetCompatibility =
            JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    composeOptions {
        kotlinCompilerExtensionVersion =
            "1.5.14"
    }

    testOptions {
        unitTests.isReturnDefaultValues = true
    }

    packaging {
        resources {
            excludes +=
                "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {

    // AndroidX
    implementation(libs.androidx.core.ktx)

    implementation(
        libs.androidx.lifecycle.runtime.ktx
    )

    implementation(
        libs.androidx.lifecycle.runtime.compose
    )

    implementation(
        libs.androidx.lifecycle.viewmodel.compose
    )

    implementation(
        libs.androidx.activity.compose
    )

    // Compose
    implementation(
        platform(libs.androidx.compose.bom)
    )

    implementation(libs.androidx.ui)

    implementation(
        libs.androidx.ui.graphics
    )

    implementation(
        libs.androidx.ui.tooling.preview
    )

    implementation(
        libs.androidx.material3
    )

    implementation(
        libs.androidx.material.icons.extended
    )

    implementation(
        libs.androidx.navigation.compose
    )

    // Storage
    implementation(
        libs.androidx.datastore.preferences
    )

    // Kotlin Coroutines
    implementation(
        libs.kotlinx.coroutines.android
    )

    // Kotlin Serialization
    implementation(
        libs.kotlinx.serialization.json
    )

    // WebSocket / HTTP
    implementation(
        libs.okhttp
    )

    // Security
    implementation(
        libs.androidx.security.crypto
    )

    // Debug
    debugImplementation(
        libs.androidx.ui.tooling
    )

    debugImplementation(
        libs.androidx.ui.test.manifest
    )

    // Unit tests
    testImplementation(
        libs.junit
    )

    testImplementation(
        libs.kotlinx.coroutines.test
    )

    testImplementation(
        libs.mockito.core
    )

    testImplementation(
        libs.mockito.kotlin
    )

    // Android tests
    androidTestImplementation(
        libs.androidx.test.ext.junit
    )

    androidTestImplementation(
        libs.androidx.test.espresso.core
    )

    androidTestImplementation(
        platform(libs.androidx.compose.bom)
    )

    androidTestImplementation(
        libs.androidx.ui.test.junit4
    )
}