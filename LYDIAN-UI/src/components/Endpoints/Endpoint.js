import React, { Component } from 'react'
import axios from 'axios';
import { Link } from "react-router-dom";

import { baseUrl } from '../../config';
import "react-tabulator/lib/styles.css"; // default theme
import "react-tabulator/css/bootstrap/tabulator_bootstrap.min.css"; // use Theme(s)
import { ReactTabulator, reactFormatter } from 'react-tabulator'
import { Container, Row, Col } from 'react-bootstrap'

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { library } from "@fortawesome/fontawesome-svg-core";
import { faArrowCircleLeft } from "@fortawesome/free-solid-svg-icons";

library.add(faArrowCircleLeft);

export class Endpoint extends Component {

    constructor(props) {
        super(props)

        this.state = {
            endpoint: this.props.location.state.endpoint,
            interfacesData: [],
            servicesData: [],
            threatsData: [],
            vulnerabilitiesData: []
        }
    }

    componentDidMount() {
        axios.get(baseUrl + 'api/v1/endpoints/' + this.state.endpoint + '/threats')
            .then(response => {
                this.setState({
                    threatsData: response.data
                });
            })
            .catch(function (error) {
                console.log(error);
            })
        axios.get(baseUrl + 'api/v1/endpoints/' + this.state.endpoint + '/risks')
            .then(response => {
                this.setState({
                    vulnerabilitiesData: response.data
                });
            })
            .catch(function (error) {
                console.log(error);
            })
        axios.get(baseUrl + 'api/v1/endpoints/' + this.state.endpoint + '/interfaces')
            .then(response => {
                this.setState({
                    interfacesData: response.data
                });
            })
            .catch(function (error) {
                console.log(error);
            })
        axios.get(baseUrl + 'api/v1/endpoints/' + this.state.endpoint + '/services')
            .then(response => {
                this.setState({
                    servicesData: response.data
                });
            })
            .catch(function (error) {
                console.log(error);
            })
    }

    render() {
        const threatcolumns = [
            { title: "Host", field: "host" },
            { title: "Severity", field: "severity" },
            { title: "Message", field: "message" },
        ];
        const interfacecolumns = [
            { title: "Host", field: "host" },
            { title: "If Name", field: "ifname" },
            { title: "IP", field: "ip" },
            { title: "Mac", field: "mac" },
        ];
        const servicecolumns = [
            { title: "Host", field: "host" },
            { title: "Svc Name", field: "svcname" },
            { title: "Status", field: "status" },
            { title: "Description", field: "desc" },
        ];
        const options = {
            movableRows: true,
            movableColumns: true,
            layout: "fitColumns",
        };
        
        return (
            <div>
                <Container>
                    <Link to='/Setup'>
                        <FontAwesomeIcon
                            icon="arrow-circle-left"
                            size='3x'
                            color='black'
                        />
                    </Link>
                    <br />
                    <Row className="show-grid">
                        <Col md={{ span: 8, offset: 2 }}>
                            <Row>
                                <h1 style={{ marginLeft: '350px', fontSize: 26, fontWeight: 'bold', marginBottom: '20px' }}>Interfaces Data</h1>
                                <ReactTabulator
                                    data={this.state.interfacesData}
                                    columns={interfacecolumns}
                                    tooltips={true}
                                    options={options}
                                    style={{border: "2px solid rgb(0, 0, 0)"}}
                                    data-custom-attr="test-custom-attribute"
                                    className="table-active table-light thead-dark table-striped table-primary table-bordered "
                                />
                            </Row>
                            <Row>
                                <h1 style={{ marginLeft: '350px', fontSize: 26, fontWeight: 'bold', marginBottom: '20px' }}>Services Data</h1>
                                <ReactTabulator
                                    data={this.state.servicesData}
                                    columns={servicecolumns}
                                    tooltips={true}
                                    options={options}
                                    style={{border: "2px solid rgb(0, 0, 0)"}}
                                    data-custom-attr="test-custom-attribute"
                                    className="table-active table-light thead-dark table-striped table-primary table-bordered "
                                />
                            </Row>
                            <Row>
                                <h1 style={{ marginLeft: '350px', fontSize: 26, fontWeight: 'bold', marginBottom: '20px' }}>Threats Data</h1>
                                <ReactTabulator
                                    data={this.state.threatsData}
                                    columns={threatcolumns}
                                    tooltips={true}
                                    options={options}
                                    style={{border: "2px solid rgb(0, 0, 0)"}}
                                    data-custom-attr="test-custom-attribute"
                                    className="table-active table-light thead-dark table-striped table-primary table-bordered "
                                />
                            </Row>
                            <Row>
                                <h1 style={{ marginLeft: '350px', fontSize: 26, fontWeight: 'bold', marginBottom: '20px' }}>Vulnerabilites Data</h1>
                                <ReactTabulator
                                    data={this.state.vulnerabilitiesData}
                                    columns={threatcolumns}
                                    tooltips={true}
                                    options={options}
                                    style={{border: "2px solid rgb(0, 0, 0)"}}
                                    data-custom-attr="test-custom-attribute"
                                    className="table-active table-light thead-dark table-striped table-primary table-bordered "
                                />
                            </Row>
                        </Col>
                    </Row>
                </Container>
            </div>
        )
    }
}

export default Endpoint
