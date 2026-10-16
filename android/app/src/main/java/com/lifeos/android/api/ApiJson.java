package com.lifeos.android.api;

import com.google.gson.FieldNamingPolicy;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonDeserializer;
import com.google.gson.JsonParseException;
import java.time.Instant;
import java.time.LocalDate;
import java.time.format.DateTimeParseException;

/** The one Gson configured for the API: snake_case fields, ISO dates and instants. */
final class ApiJson {

    static final Gson GSON = new GsonBuilder()
            .setFieldNamingPolicy(FieldNamingPolicy.LOWER_CASE_WITH_UNDERSCORES)
            .registerTypeAdapter(LocalDate.class, (JsonDeserializer<LocalDate>) (json, type, ctx) -> {
                if (json.isJsonNull()) {
                    return null;
                }
                try {
                    return LocalDate.parse(json.getAsString());
                } catch (DateTimeParseException e) {
                    throw new JsonParseException("Invalid date: " + json, e);
                }
            })
            .registerTypeAdapter(Instant.class, (JsonDeserializer<Instant>) (json, type, ctx) -> {
                if (json.isJsonNull()) {
                    return null;
                }
                try {
                    return Instant.parse(json.getAsString());
                } catch (DateTimeParseException e) {
                    throw new JsonParseException("Invalid timestamp: " + json, e);
                }
            })
            .create();

    private ApiJson() {}
}
