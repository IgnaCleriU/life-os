package com.lifeos.android.api.model;

import com.google.gson.annotations.SerializedName;

/** Priority of a {@link Task}; {@link #value()} is the wire value. */
public enum Priority {
    @SerializedName("low") LOW("low"),
    @SerializedName("medium") MEDIUM("medium"),
    @SerializedName("high") HIGH("high");

    private final String value;

    Priority(String value) {
        this.value = value;
    }

    public String value() {
        return value;
    }
}
