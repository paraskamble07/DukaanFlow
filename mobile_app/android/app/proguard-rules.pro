# ProGuard / R8 rules consumed automatically by Flutter's Gradle plugin for
# release builds (see FlutterPlugin.kt — proguard-rules.pro in :app is added
# whenever resource shrinking / minification is enabled).

# ---------------------------------------------------------------------------
# Room: generated *_Impl classes are instantiated reflectively.
#
# Room's RoomDatabase.Builder looks up "<package>.<Name>_Impl" via
# Class.forName and calls its no-arg constructor via reflection. R8 sees no
# direct program reference to that constructor and strips it, which makes
# Room throw:
#   RuntimeException: Failed to create an instance of
#   androidx.work.impl.WorkDatabase
# This happens at process start through androidx.startup / AdMob's
# initializer (which depends on WorkManager), i.e. before Flutter runs, so it
# killed the app on launch (confirmed: the released classes.dex contained
# WorkDatabase_Impl with NO constructor).
-keep class * extends androidx.room.RoomDatabase { <init>(); }

# WorkManager ships its own Room database (androidx.work.impl.WorkDatabase);
# keep it explicitly as well, in case a future AGP/R8 version treats the
# generalized rule above differently.
-keep class androidx.work.impl.WorkDatabase { <init>(); }
-keep class androidx.work.impl.WorkDatabase_Impl { <init>(); }

# AndroidX WorkManager + Room also construct helper/callback types by name.
-keep class androidx.work.impl.WorkSqliteOpenHelper$Callback { <init>(); }
