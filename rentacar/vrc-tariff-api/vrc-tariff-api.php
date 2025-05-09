<?php
/**
 * Plugin Name:     VikRentCar Tariff Updater & Reader API
 * Plugin URI:      https://example.com/
 * Description:     Exposes secure REST endpoints to list cars, read tariffs, and batch-update VikRentCar tariffs.
 * Version:         1.6
 * Author:          Your Name
 * Author URI:      https://example.com/
 */

// Register all routes on REST init
add_action( 'rest_api_init', function() {
    // POST /wp-json/vikrentcar/v1/tariffs
    register_rest_route( 'vikrentcar/v1', '/tariffs', [
        [
            'methods'             => 'POST',
            'callback'            => 'vrc_update_tariffs',
            'permission_callback' => function( WP_REST_Request $req ) {
                return current_user_can( 'manage_options' );
            },
        ],
        [
            'methods'             => 'GET',
            'callback'            => 'vrc_get_tariffs',
            'permission_callback' => function() {
                return current_user_can( 'manage_options' );
            },
            'args'                => [
                'car_id' => [
                    'required'          => true,
                    'validate_callback' => function( $param ) {
                        return is_numeric( $param ) && intval( $param ) > 0;
                    },
                ],
            ],
        ],
    ] );

    // GET /wp-json/vikrentcar/v1/cars
    register_rest_route( 'vikrentcar/v1', '/cars', [
        'methods'             => 'GET',
        'callback'            => 'vrc_list_cars',
        'permission_callback' => function() {
            return current_user_can( 'manage_options' );
        },
    ] );
} );

/**
 * POST /wp-json/vikrentcar/v1/tariffs
 * Body: { car_id: int, prices: { dayCount: price, … } }
 */
function vrc_update_tariffs( WP_REST_Request $req ) {
    global $wpdb;
    $table  = $wpdb->prefix . 'vikrentcar_dispcost';

    $body   = $req->get_json_params();
    $car_id = isset( $body['car_id'] ) ? intval( $body['car_id'] ) : 0;
    $prices = isset( $body['prices'] ) && is_array( $body['prices'] )
              ? $body['prices']
              : [];

    if ( $car_id < 1 || empty( $prices ) ) {
        return new WP_Error(
            'invalid_payload',
            'car_id must be > 0 and prices must be a non-empty object',
            [ 'status' => 400 ]
        );
    }

    $updated = 0;
    foreach ( $prices as $days => $price ) {
        $d = intval( $days );
        $c = floatval( $price );

        $res = $wpdb->update(
            $table,
            [ 'cost'  => $c ],                  // update the cost column
            [ 'idcar' => $car_id,               // match on idcar
              'days'  => $d ],                  // match on days
            [ '%f' ],
            [ '%d', '%d' ]
        );

        if ( $res !== false ) {
            $updated += $res;
        }
    }

    return rest_ensure_response([
        'success'      => true,
        'rows_updated' => $updated,
    ]);
}

/**
 * GET /wp-json/vikrentcar/v1/tariffs?car_id=7
 */
function vrc_get_tariffs( WP_REST_Request $req ) {
    global $wpdb;
    $car_id = intval( $req->get_param( 'car_id' ) );
    $table  = $wpdb->prefix . 'vikrentcar_dispcost';

    $rows = $wpdb->get_results(
        $wpdb->prepare(
            "SELECT days AS day, cost FROM {$table} WHERE idcar = %d ORDER BY days ASC",
            $car_id
        ),
        ARRAY_A
    );

    if ( $wpdb->last_error ) {
        return new WP_Error(
            'db_error',
            $wpdb->last_error,
            [ 'status' => 500 ]
        );
    }

    return rest_ensure_response( $rows );
}

/**
 * GET /wp-json/vikrentcar/v1/cars
 */
function vrc_list_cars( WP_REST_Request $req ) {
    global $wpdb;
    $table = $wpdb->prefix . 'vikrentcar_cars';

    $rows = $wpdb->get_results(
        "
        SELECT
            `id`   AS idcar,
            `name` AS name
          FROM `{$table}`
         ORDER BY `name` ASC
        ",
        ARRAY_A
    );

    if ( $wpdb->last_error ) {
        return new WP_Error(
            'db_error',
            $wpdb->last_error,
            [ 'status' => 500 ]
        );
    }

    return rest_ensure_response( $rows );
}
