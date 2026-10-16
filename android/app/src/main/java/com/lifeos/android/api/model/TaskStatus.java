package com.lifeos.android.api.model;

import com.google.gson.annotations.SerializedName;

/** Board column of a {@link Task}; {@link #value()} is the wire value. */
public enum TaskStatus {
    @SerializedName("todo") TODO("todo"),
    @SerializedName("doing") DOING("doing"),
    @SerializedName("done") DONE("done");

    private final String value;

    TaskStatus(String value) {
        this.value = value;
    }

    public String value() {
        return value;
    }
}
