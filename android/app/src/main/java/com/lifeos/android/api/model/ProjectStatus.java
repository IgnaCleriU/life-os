package com.lifeos.android.api.model;

import com.google.gson.annotations.SerializedName;

/** Lifecycle of a {@link Project}; {@link #value()} is the wire value. */
public enum ProjectStatus {
    @SerializedName("active") ACTIVE("active"),
    @SerializedName("completed") COMPLETED("completed"),
    @SerializedName("archived") ARCHIVED("archived");

    private final String value;

    ProjectStatus(String value) {
        this.value = value;
    }

    public String value() {
        return value;
    }
}
