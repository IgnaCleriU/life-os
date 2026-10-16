package lifeos.adapters.rest;

import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.function.Function;

/**
 * Conversión de los valores crudos del request a tipos de dominio. Cualquier
 * valor inválido termina en {@link RequestValidationException} (422), igual que
 * la validación de Pydantic en el adapter Python.
 */
final class RequestParsing {

    private RequestParsing() {}

    static String required(String field, String value) {
        if (value == null) {
            throw new RequestValidationException("Falta el campo requerido '" + field + "'");
        }
        return value;
    }

    static <T> T parse(String field, String value, Function<String, T> parser) {
        if (value == null) {
            return null;
        }
        try {
            return parser.apply(value);
        } catch (IllegalArgumentException | DateTimeParseException e) {
            throw new RequestValidationException("Valor inválido para '" + field + "': " + value);
        }
    }

    static <T> List<T> parseAll(String field, List<String> values, Function<String, T> parser) {
        return values == null ? null : values.stream().map(value -> parse(field, value, parser)).toList();
    }

    static UUID uuid(String field, String value) {
        return parse(field, value, UUID::fromString);
    }

    static LocalDate date(String field, String value) {
        return parse(field, value, LocalDate::parse);
    }

    /** Valor de un campo de un body PATCH ya presente: debe ser string o null. */
    static String patchString(Map<String, Object> body, String field) {
        Object value = body.get(field);
        if (value != null && !(value instanceof String)) {
            throw new RequestValidationException("'" + field + "' debe ser un string");
        }
        return (String) value;
    }
}
