package lifeos.adapters.rest;

import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.function.Function;
import java.util.regex.Pattern;

/**
 * Conversión de los valores crudos del request a tipos de dominio. Cualquier
 * valor inválido termina en {@link RequestValidationException} (422), igual que
 * la validación de Pydantic en el adapter Python.
 */
final class RequestParsing {

    /** Forma canónica 8-4-4-4-12; {@link UUID#fromString} acepta cosas como {@code 1-1-1-1-1}. */
    private static final Pattern CANONICAL_UUID =
            Pattern.compile("[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}");

    private RequestParsing() {}

    /** Parser estricto de UUID, también registrado para los path variables en {@link WebConfiguration}. */
    static UUID canonicalUuid(String value) {
        if (!CANONICAL_UUID.matcher(value).matches()) {
            throw new IllegalArgumentException("UUID inválido: " + value);
        }
        return UUID.fromString(value);
    }

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

    /**
     * Valores de un parámetro repetible ({@code ?status=a&status=b}), tomados
     * crudos de {@code getParameterValues}: {@code @RequestParam List<String>}
     * los separaría por comas y FastAPI no lo hace. Un filtro presente pero vacío
     * ({@code ?status=}) llega como {@code [""]} y lo rechaza el parser: es
     * inválido, no "sin filtro".
     */
    static <T> List<T> parseAll(String field, String[] rawValues, Function<String, T> parser) {
        if (rawValues == null) {
            return null;
        }
        return List.of(rawValues).stream().map(value -> parse(field, value, parser)).toList();
    }

    static UUID uuid(String field, String value) {
        return parse(field, value, RequestParsing::canonicalUuid);
    }

    static LocalDate date(String field, String value) {
        return parse(field, value, LocalDate::parse);
    }

    /**
     * Campo de texto de un body JSON (ausente o null → null). Los bodies se leen
     * como mapa para que un número no se convierta en string en silencio, como
     * haría Jackson; Pydantic lo rechaza con 422.
     */
    static String string(Map<String, Object> body, String field) {
        Object value = body.get(field);
        if (value != null && !(value instanceof String)) {
            throw new RequestValidationException("'" + field + "' debe ser un string");
        }
        return (String) value;
    }
}
