# Gson maps JSON onto the fields of these classes by reflection, so R8 must
# neither rename nor remove them (nor the enum constants and their
# @SerializedName values).
-keepattributes Signature, *Annotation*, EnclosingMethod, InnerClasses
-keep class com.lifeos.android.api.model.** { *; }
-keepclassmembers enum com.lifeos.android.api.model.** { *; }
